"""Query Engine: Hybrid search, RRF fusion, re-ranking, logging, and feedback-boosted RAG.

Retrieval pipeline:
  1. Metadata lookup: extract words from query, look them up in ChromaDB metadata
     — works for ANY column name (SAP: BUKRS, MATNR; obfuscated: flg_5nq; normal: patient_id)
  2. Semantic search: ChromaDB cosine similarity per collection
  3. Reciprocal Rank Fusion: merge results across collections
  4. Feedback boost: upweight chunks from previously helpful answers
  5. Score threshold + cap: filter low-quality, keep top 10
  6. Context enrichment: re-attach stats from metadata for Claude
  7. Generation: Claude API with enriched context
  8. Logging: structured JSONL with latency, scores, quality flags
"""

import json
import os
import re
import time
import uuid
import anthropic
import chromadb


PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
CHROMA_DIR = os.path.join(PROJECT_DIR, "chroma_db")
LOG_FILE = os.path.join(PROJECT_DIR, "query_log.jsonl")
FEEDBACK_CACHE_FILE = os.path.join(PROJECT_DIR, "feedback_cache.json")

COLLECTIONS = ["data_dictionary", "ontology", "lineage", "pbi_lineage", "pbi_catalog"]

MIN_SCORE_THRESHOLD = 0.15
MAX_RESULTS_FOR_CLAUDE = 10
RRF_K = 60
FEEDBACK_SIMILARITY_THRESHOLD = 0.6

# Common English words to skip during metadata lookup
STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "must", "need",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us",
    "my", "your", "his", "its", "our", "their",
    "this", "that", "these", "those", "what", "which", "who", "whom", "how",
    "where", "when", "why", "if", "then", "else", "than", "so", "as",
    "and", "or", "but", "not", "no", "nor",
    "in", "on", "at", "to", "for", "with", "by", "from", "of", "about",
    "into", "through", "between", "after", "before", "above", "below",
    "all", "each", "every", "both", "few", "more", "most", "some", "any",
    "tell", "show", "give", "get", "find", "list", "describe", "explain",
    "mean", "means", "called", "used", "using", "across", "layer", "layers",
    "column", "columns", "table", "tables", "view", "views", "data",
    "bronze", "silver", "gold", "schema", "database", "pipeline",
    "type", "name", "value", "values", "description",
}


# --- Metadata Lookup (replaces regex-based keyword detection) ---

def extract_candidate_tokens(question):
    """Extract potential column/table identifiers from the question.

    No regex patterns for specific naming conventions.
    Simply tokenizes the question, removes common English words,
    and returns candidates to look up in ChromaDB metadata.

    Works for ANY naming convention:
      - SAP: BUKRS, MATNR, VBELN
      - Obfuscated: flg_5nq, cod_c6u
      - Normal: patient_id, bill_amount
      - Anything else a developer might name a column
    """
    # Split on whitespace and punctuation, keep underscores and alphanumeric
    raw_tokens = question.replace(",", " ").replace("?", " ").replace(".", " ").split()

    candidates = set()
    for token in raw_tokens:
        # Strip quotes and surrounding punctuation
        clean = token.strip("'\"`()[]{}!@#$%^&*")
        if not clean:
            continue
        # Skip pure numbers and very short tokens (1 char)
        if clean.isdigit() or len(clean) <= 1:
            continue
        # Skip common English words
        if clean.lower() in STOP_WORDS:
            continue
        candidates.add(clean)
        # Also add lowercase version for case-insensitive lookup
        if clean != clean.lower():
            candidates.add(clean.lower())

    return list(candidates)


def metadata_lookup(client, candidates):
    """Look up candidate tokens in ChromaDB metadata.

    For each candidate, check if it exists as:
      - A column name (in data_dictionary collection)
      - An original/source column name (in data_dictionary collection)
      - A source column (in lineage collection)
      - A silver column (in lineage collection)
      - A gold column (in lineage collection)
      - An entity name (in ontology collection)

    If ChromaDB returns results, it's a real identifier — include it.
    If not, skip it — let semantic search handle it.

    This works for ANY column naming convention without hardcoded patterns.
    """
    forced = []
    seen_docs = set()  # dedup by document text prefix

    def _add_results(collection_name, results, score):
        for doc, meta in zip(results.get("documents", []), results.get("metadatas", [])):
            doc_key = doc[:100]
            if doc_key not in seen_docs:
                seen_docs.add(doc_key)
                forced.append({
                    "collection": collection_name,
                    "document": doc,
                    "metadata": meta,
                    "score": score,
                    "source": "keyword",
                })

    # Search data_dictionary
    try:
        dd_collection = client.get_collection("data_dictionary")
        for token in candidates:
            # Check as column name (exact match)
            results = dd_collection.get(where={"column": token}, include=["documents", "metadatas"])
            _add_results("data_dictionary", results, 1.0)

            # Check as original/source column name
            results = dd_collection.get(where={"original_name": token}, include=["documents", "metadatas"])
            _add_results("data_dictionary", results, 0.95)
    except Exception:
        pass

    # Search lineage
    try:
        lineage_collection = client.get_collection("lineage")
        for token in candidates:
            # Check as source column
            results = lineage_collection.get(where={"source_column": token}, include=["documents", "metadatas"])
            _add_results("lineage", results, 0.95)

            # Check as silver column
            results = lineage_collection.get(where={"silver_column": token}, include=["documents", "metadatas"])
            _add_results("lineage", results, 0.95)

            # Check as gold column
            results = lineage_collection.get(where={"gold_column": token}, include=["documents", "metadatas"])
            _add_results("lineage", results, 0.90)
    except Exception:
        pass

    # Search ontology for entity names
    try:
        ont_collection = client.get_collection("ontology")
        for token in candidates:
            results = ont_collection.get(where={"entity": token.title()}, include=["documents", "metadatas"])
            _add_results("ontology", results, 0.90)
    except Exception:
        pass

    # Search pbi_lineage for PBI columns, gold columns, bronze columns
    try:
        pbi_lin = client.get_collection("pbi_lineage")
        for token in candidates:
            for field, score in [("pbi_column", 0.95), ("gold_column", 0.90),
                                 ("bronze_column", 0.90), ("source_column", 0.90)]:
                results = pbi_lin.get(where={field: token}, include=["documents", "metadatas"])
                _add_results("pbi_lineage", results, score)

        # When query mentions "end-to-end" or "pbi lineage", boost e2e docs
        pbi_lineage_keywords = {"end-to-end", "e2e", "pbi", "powerbi", "power"}
        if any(t.lower() in pbi_lineage_keywords for t in candidates):
            results = pbi_lin.get(where={"type": "pbi_end_to_end"}, include=["documents", "metadatas"])
            _add_results("pbi_lineage", results, 0.85)
    except Exception:
        pass

    # Search pbi_catalog for PBI columns, measures, reports, dashboards
    try:
        pbi_cat = client.get_collection("pbi_catalog")
        for token in candidates:
            for field, score in [("pbi_column", 0.95), ("measure_name", 0.95),
                                 ("report_name", 0.90), ("dashboard_name", 0.90)]:
                results = pbi_cat.get(where={field: token}, include=["documents", "metadatas"])
                _add_results("pbi_catalog", results, score)

        # PBI artifact type lookup: when query mentions "dashboard", "report", etc.,
        # fetch all docs of that type so they get keyword-level boost in RRF
        pbi_type_keywords = {
            "dashboard": "pbi_dashboard", "dashboards": "pbi_dashboard",
            "report": "pbi_report", "reports": "pbi_report",
            "measure": "pbi_measure", "measures": "pbi_measure",
            "kpi": "pbi_measure", "dax": "pbi_measure",
            "calculated": "pbi_measure", "formula": "pbi_measure",
            "tile": "pbi_dashboard", "tiles": "pbi_dashboard",
            "revenue": "pbi_measure", "copay": "pbi_measure",
            "coverage": "pbi_measure", "count": "pbi_measure",
        }
        for token in candidates:
            pbi_type = pbi_type_keywords.get(token.lower())
            if pbi_type:
                results = pbi_cat.get(where={"type": pbi_type}, include=["documents", "metadatas"])
                _add_results("pbi_catalog", results, 0.90)
    except Exception:
        pass

    # Detect broad overview queries and force-retrieve the catalog summary
    overview_keywords = {"overview", "summary", "catalog", "available", "knowledge", "mesh"}
    if any(t.lower() in overview_keywords for t in candidates):
        try:
            dd_col = client.get_collection("data_dictionary")
            results = dd_col.get(
                where={"type": "catalog_summary"},
                include=["documents", "metadatas"],
            )
            _add_results("data_dictionary", results, 1.0)
        except Exception:
            pass

    return forced


# --- Semantic Search ---

def semantic_search(client, question, top_k=7):
    """Search all ChromaDB collections with score capture."""
    per_collection_results = {}

    for collection_name in COLLECTIONS:
        try:
            collection = client.get_collection(collection_name)
            count = collection.count()
            if count == 0:
                continue
            results = collection.query(
                query_texts=[question],
                n_results=min(top_k, count),
                include=["documents", "metadatas", "distances"],
            )
            ranked = []
            for doc, metadata, distance in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                score = max(0.0, 1.0 - distance)
                ranked.append({
                    "collection": collection_name,
                    "document": doc,
                    "metadata": metadata,
                    "score": score,
                    "source": "semantic",
                })
            per_collection_results[collection_name] = ranked
        except Exception as e:
            print(f"[Query] Warning: Could not search {collection_name}: {e}")

    return per_collection_results


# --- Reciprocal Rank Fusion ---

def reciprocal_rank_fusion(per_collection_results, keyword_results, k=RRF_K):
    """Fuse ranked results from multiple collections using RRF.

    Each document gets: RRF_score = sum(1 / (k + rank)) across all lists it appears in.
    Keyword matches get a bonus via their pre-assigned high scores.
    """
    scores = {}
    doc_map = {}

    # Score keyword results (they come pre-scored)
    for chunk in keyword_results:
        doc_id = _chunk_id(chunk)
        scores[doc_id] = scores.get(doc_id, 0.0) + chunk["score"]
        doc_map[doc_id] = chunk

    # Score semantic results per collection
    for ranked_list in per_collection_results.values():
        for rank, chunk in enumerate(ranked_list):
            doc_id = _chunk_id(chunk)
            rrf_score = 1.0 / (k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0.0) + rrf_score
            # Prefer higher-detail version if duplicate
            if doc_id not in doc_map or chunk["score"] > doc_map[doc_id].get("score", 0):
                doc_map[doc_id] = chunk

    # Sort by fused score
    sorted_ids = sorted(scores.keys(), key=lambda d: scores[d], reverse=True)
    result = []
    for doc_id in sorted_ids:
        chunk = doc_map[doc_id]
        chunk["rrf_score"] = round(scores[doc_id], 4)
        result.append(chunk)

    return result


def _chunk_id(chunk):
    """Generate a dedup key for a chunk based on collection + first 100 chars of doc."""
    return f"{chunk['collection']}:{chunk['document'][:100]}"


# --- Feedback Cache ---

def load_feedback_cache():
    """Load the feedback cache from disk."""
    if os.path.exists(FEEDBACK_CACHE_FILE):
        try:
            with open(FEEDBACK_CACHE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception):
            pass
    return {"approved_pairs": []}


def save_feedback_cache(cache):
    """Save the feedback cache to disk."""
    with open(FEEDBACK_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def apply_feedback_boost(fused_results, question):
    """Boost scores of chunks that helped answer semantically similar past questions.

    Uses ChromaDB embedding similarity (not word overlap) to find similar past
    approved questions. This handles cases where questions use different words
    but have the same intent (e.g., "How is out_of_pocket calculated?" vs
    "What is the formula for patient copay?").
    """
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        fb_collection = client.get_collection("feedback_questions")
        if fb_collection.count() == 0:
            return fused_results
    except Exception:
        return fused_results  # collection doesn't exist yet

    results = fb_collection.query(
        query_texts=[question],
        n_results=min(5, fb_collection.count()),
        include=["metadatas", "distances"],
    )

    good_chunk_ids = set()
    for metadata, distance in zip(results["metadatas"][0], results["distances"][0]):
        similarity = max(0.0, 1.0 - distance)
        if similarity >= FEEDBACK_SIMILARITY_THRESHOLD:
            chunk_ids_str = metadata.get("good_chunk_ids", "")
            if chunk_ids_str:
                good_chunk_ids.update(chunk_ids_str.split("|||"))

    if not good_chunk_ids:
        return fused_results

    # Boost matching chunks
    for chunk in fused_results:
        chunk_id = _chunk_id(chunk)
        if chunk_id in good_chunk_ids:
            chunk["rrf_score"] = chunk.get("rrf_score", 0) + 0.5
            chunk["feedback_boosted"] = True

    # Re-sort
    fused_results.sort(key=lambda x: x.get("rrf_score", 0), reverse=True)
    return fused_results


def record_feedback(query_id, question, chunk_ids, helpful):
    """Record user feedback and update the cache.

    When helpful, stores the question in a ChromaDB collection for
    semantic similarity matching in future queries.
    """
    cache = load_feedback_cache()
    if helpful:
        cache["approved_pairs"].append({
            "query_id": query_id,
            "question": question,
            "good_chunk_ids": chunk_ids,
            "timestamp": time.time(),
        })
        # Keep last 100 entries
        cache["approved_pairs"] = cache["approved_pairs"][-100:]

        # Store in ChromaDB for semantic feedback matching
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        fb_collection = client.get_or_create_collection("feedback_questions")
        fb_collection.upsert(
            documents=[question],
            metadatas=[{
                "good_chunk_ids": "|||".join(chunk_ids),
                "query_id": query_id,
            }],
            ids=[f"fb_{query_id}"],
        )
    save_feedback_cache(cache)

    # Also log the feedback event
    log_event({
        "type": "feedback",
        "query_id": query_id,
        "question": question,
        "helpful": helpful,
    })


# --- Context Enrichment ---

def format_chunk_for_context(chunk):
    """Format a chunk for Claude's context, re-attaching stats from metadata."""
    meta = chunk.get("metadata", {})
    base = f"[{chunk['collection']}] {chunk['document']}"

    # Re-attach stats from metadata for data_dictionary entries
    stats_parts = []
    if meta.get("type") == "data_dictionary":
        if "null_pct" in meta:
            stats_parts.append(f"Null%: {meta['null_pct']}")
        if "unique_count" in meta:
            stats_parts.append(f"Unique Count: {meta['unique_count']}")
        if "sample_values" in meta:
            stats_parts.append(f"Samples: {meta['sample_values']}")

    if stats_parts:
        base += " | " + " | ".join(stats_parts)

    return base


# --- Logging ---

def log_event(event):
    """Append a structured event to the JSONL query log."""
    event["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(event, default=str) + "\n")
    except Exception:
        pass


def assess_quality(top_scores):
    """Assess retrieval quality based on top-3 scores."""
    if not top_scores:
        return "NONE"
    avg = sum(top_scores[:3]) / min(len(top_scores), 3)
    if avg > 0.6:
        return "HIGH"
    elif avg > 0.3:
        return "MEDIUM"
    return "LOW"


# --- Query Routing ---

def route_query(question):
    """Pick LLM model based on query complexity.

    Complex queries (multi-hop, comparisons, traces) get Sonnet for deeper reasoning.
    Simple lookups (what is, describe, list) get Haiku for speed and cost savings.
    """
    q = question.lower()

    complex_keywords = ["compare", "trace", "end-to-end", "explain how",
                        "relationship between", "impact", "all layers",
                        "difference between", "why", "analyze"]
    if any(kw in q for kw in complex_keywords):
        return "claude-sonnet-4-6"

    simple_keywords = ["what is", "what does", "list", "describe", "show me",
                       "what are", "how many", "what's"]
    if any(kw in q for kw in simple_keywords):
        return "claude-haiku-4-5-20251001"

    return "claude-sonnet-4-6"  # default mid-tier


# --- Citation Verification ---

def verify_citations(answer, num_chunks):
    """Check that all cited chunk numbers reference actual chunks."""
    cited = set(int(n) for n in re.findall(r'\[(\d+)\]', answer))
    if not cited:
        return True, []  # no citations used
    invalid = [n for n in cited if n < 1 or n > num_chunks]
    return len(invalid) == 0, invalid


# --- Hallucination Detection ---

def check_hallucination(question, answer, context_chunks):
    """Quick LLM check: is every claim in the answer supported by the context?

    Uses a cheap Haiku call to verify grounding. Returns (is_grounded, details).
    """
    client = anthropic.Anthropic()
    context = "\n".join(
        f"[{i+1}] {c['document']}" for i, c in enumerate(context_chunks)
    )

    result = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": (
                f"Source documents:\n{context}\n\n"
                f"Answer to verify:\n{answer}\n\n"
                "List any claims in the answer that are NOT supported by the source "
                "documents above. If ALL claims are supported, respond with exactly: GROUNDED"
            ),
        }],
    )
    response = result.content[0].text.strip()
    is_grounded = "GROUNDED" in response
    return is_grounded, response


# --- Generation ---

def _build_system_prompt():
    """Build the system prompt for the RAG generation step."""
    return (
        "You are a data analyst assistant for an enterprise data pipeline. "
        "The pipeline has three layers: Bronze (raw ingestion from source systems), "
        "Silver (transformed and joined tables), and Gold (business-ready views). "
        "Column names across layers may not be self-explanatory — they could be "
        "system-generated codes, abbreviations, or technical identifiers from source "
        "systems like SAP, Salesforce, or internal databases.\n\n"
        "You have access to a data catalog with:\n"
        "- Data dictionary: column descriptions, data types, sample values, statistics\n"
        "- Lineage: how each column flows from source through Bronze -> Silver -> Gold, "
        "including the SQL expressions used for transformations\n"
        "- Ontology: entity definitions and relationships between tables\n"
        "- Power BI layer: PBI reports, dashboards, measures (with DAX formulas), "
        "column mappings to Gold views, and end-to-end lineage from PBI visuals "
        "back to source CSV files\n\n"
        "Use ONLY the provided context to answer questions. Do not guess or assume "
        "information that is not in the context.\n\n"
        "IMPORTANT RULES:\n"
        "1. When a column name is not self-explanatory, use the data dictionary "
        "description and lineage to explain what it represents and where it comes from.\n"
        "2. When the user asks about analysis or dashboards, first identify which columns "
        "in the existing tables COULD be relevant based on their metadata. "
        "Clearly state what columns exist and what they contain. "
        "Then explain what additional data might be needed if the existing columns "
        "are not sufficient.\n"
        "3. If the user asks about data or fields that do NOT exist in the catalog, "
        "clearly state that and list what IS available.\n"
        "4. Always be explicit about what you KNOW (from the metadata) "
        "vs what you are ASSUMING.\n"
        "5. When explaining lineage, show the full chain: "
        "source -> Bronze -> Silver -> Gold, including any transformations applied.\n"
        "6. When a question involves Power BI, include the PBI artifact details: "
        "which dashboard/tile shows the data, which report and dataset it belongs to, "
        "the DAX formula for measures, and the Gold view it sources from.\n"
        "7. When the user asks a broad overview question (e.g., 'what is available', "
        "'what do you know', 'summarize the catalog'), look for a CATALOG SUMMARY "
        "document in the context. Use its counts and details to give a comprehensive "
        "overview of all data domains. Do not guess numbers — cite only what the "
        "summary document provides.\n"
        "8. CITATION RULES: Each context chunk is numbered [1], [2], etc. "
        "Every factual claim in your answer MUST include a citation like [1]. "
        "If you cannot cite a source for a claim, do not make that claim. "
        "End your answer with a 'Sources:' section listing each cited chunk number "
        "and a brief description of what it contains."
    )


def ask_claude(question, context_chunks, model=None):
    """Send question + numbered context to Claude API with citation rules."""
    client = anthropic.Anthropic()
    model = model or route_query(question)

    context = "\n\n---\n\n".join(
        f"[{i+1}] {format_chunk_for_context(chunk)}"
        for i, chunk in enumerate(context_chunks)
    )

    system_prompt = _build_system_prompt()

    message = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": f"Context from the data catalog:\n\n{context}\n\n---\n\nQuestion: {question}",
            }
        ],
    )

    return model, message.content[0].text


def ask_claude_streaming(question, context_chunks, model=None):
    """Stream Claude's response token by token. Returns (model, full_text)."""
    client = anthropic.Anthropic()
    model = model or route_query(question)

    context = "\n\n---\n\n".join(
        f"[{i+1}] {format_chunk_for_context(chunk)}"
        for i, chunk in enumerate(context_chunks)
    )

    # Reuse the same system prompt as ask_claude
    system_prompt = _build_system_prompt()

    full_response = ""
    with client.messages.stream(
        model=model,
        max_tokens=2048,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": f"Context from the data catalog:\n\n{context}\n\n---\n\nQuestion: {question}",
            }
        ],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            full_response += text
    print()  # newline after streaming

    return model, full_response


# --- MMR Diversity Selection ---

MMR_LAMBDA = 0.5


def _doc_similarity(doc_a, doc_b):
    """Estimate content similarity using metadata overlap.

    Same collection + overlapping metadata = high similarity.
    Different collection = lower similarity (diverse content).
    """
    sim = 0.0
    # Same collection = base similarity 0.5
    if doc_a.get("collection") == doc_b.get("collection"):
        sim += 0.5
    meta_a = doc_a.get("metadata", {})
    meta_b = doc_b.get("metadata", {})
    # Same type within collection = additional 0.2
    if meta_a.get("type") == meta_b.get("type"):
        sim += 0.2
    # Overlapping key metadata values = additional up to 0.3
    overlap_keys = ["pbi_table", "pbi_column", "gold_view", "table", "column"]
    matches = sum(1 for k in overlap_keys
                  if meta_a.get(k) and meta_a.get(k) == meta_b.get(k))
    sim += min(0.3, matches * 0.1)
    return min(1.0, sim)


def _mmr_select(candidates, max_results, lambda_param=MMR_LAMBDA):
    """Select diverse results using Maximal Marginal Relevance.

    Iteratively picks the candidate that maximizes:
      MMR = (1 - λ) × relevance  −  λ × max_similarity_to_already_selected
    This balances relevance with diversity — redundant docs from the same
    collection/type are penalized, promoting cross-collection coverage.
    """
    if not candidates:
        return []
    selected = [candidates[0]]  # highest-scored first
    remaining = list(candidates[1:])

    while len(selected) < max_results and remaining:
        best_score = -float("inf")
        best_idx = 0
        for i, cand in enumerate(remaining):
            relevance = cand.get("rrf_score", 0)
            max_sim = max((_doc_similarity(cand, s) for s in selected), default=0)
            mmr = (1 - lambda_param) * relevance - lambda_param * max_sim
            if mmr > best_score:
                best_score = mmr
                best_idx = i
        selected.append(remaining.pop(best_idx))
    return selected


# --- Main Query Pipeline ---

def search_vectorstore(question, top_k=7):
    """Full hybrid retrieval pipeline: keyword + semantic + RRF + feedback boost."""
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Step 1: Metadata lookup — extract tokens, look them up in ChromaDB
    candidates = extract_candidate_tokens(question)
    keyword_results = metadata_lookup(client, candidates)

    # Step 2: Semantic search per collection
    per_collection = semantic_search(client, question, top_k=top_k)

    # Step 3: Reciprocal Rank Fusion
    fused = reciprocal_rank_fusion(per_collection, keyword_results)

    # Step 4: Feedback boost from past approved answers
    fused = apply_feedback_boost(fused, question)

    # Step 5: Score threshold + cap with collection diversity
    filtered = [c for c in fused if c.get("rrf_score", 0) >= MIN_SCORE_THRESHOLD]
    if not filtered and fused:
        filtered = fused[:3]  # always return something

    # Step 6a: MMR diversity selection — pick docs that are both relevant AND
    # different from already-selected docs (prevents one collection dominating)
    top_results = _mmr_select(filtered, MAX_RESULTS_FOR_CLAUDE)

    # Step 6b: Slot safety net — guarantee at least 1 result per collection
    # that had matching results (catches edge cases MMR might miss)
    top_collections = {c["collection"] for c in top_results}
    all_filtered_collections = {c["collection"] for c in filtered}
    missing = all_filtered_collections - top_collections

    for coll in missing:
        coll_results = [c for c in filtered if c["collection"] == coll]
        if coll_results and top_results:
            top_results[-1] = coll_results[0]  # replace lowest-scored
            top_results.sort(key=lambda x: x.get("rrf_score", 0), reverse=True)

    return top_results


def query(question, stream=False):
    """Full RAG pipeline: search -> route -> generate -> verify -> log.

    Pipeline steps:
      1. Hybrid retrieval (keyword + semantic + RRF + MMR)
      2. Query routing (pick Haiku vs Sonnet based on complexity)
      3. Generation with citation rules
      4. Citation verification (do [1], [2] refs exist?)
      5. Hallucination detection (quick Haiku grounding check)
      6. Enhanced logging
    """
    query_id = str(uuid.uuid4())[:8]
    print(f"\n[Query] Searching for: {question}")

    t0 = time.time()

    # Step 1: Retrieve relevant context
    context_chunks = search_vectorstore(question)
    retrieval_ms = int((time.time() - t0) * 1000)

    if not context_chunks:
        log_event({
            "type": "query",
            "query_id": query_id,
            "question": question,
            "chunks_retrieved": 0,
            "retrieval_quality": "NONE",
            "retrieval_ms": retrieval_ms,
        })
        return query_id, "No relevant information found in the data catalog."

    top_scores = [c.get("rrf_score", 0) for c in context_chunks[:3]]
    quality = assess_quality([c.get("score", 0) for c in context_chunks])

    keyword_count = sum(1 for c in context_chunks if c.get("source") == "keyword")
    boosted_count = sum(1 for c in context_chunks if c.get("feedback_boosted"))

    print(f"[Query] Found {len(context_chunks)} relevant chunks "
          f"(keyword: {keyword_count}, semantic: {len(context_chunks) - keyword_count}, "
          f"feedback-boosted: {boosted_count})")

    # Step 2-3: Route to model + generate answer (with citations)
    t1 = time.time()
    if stream:
        model_used, answer = ask_claude_streaming(question, context_chunks)
    else:
        model_used, answer = ask_claude(question, context_chunks)
    generation_ms = int((time.time() - t1) * 1000)
    print(f"[Query] Model: {model_used} | Generation: {generation_ms}ms")

    # Step 4: Citation verification
    citations_valid, invalid_citations = verify_citations(answer, len(context_chunks))
    if not citations_valid:
        print(f"[Query] Warning: invalid citations {invalid_citations}")

    # Step 5: Hallucination detection
    t2 = time.time()
    is_grounded, grounding_details = check_hallucination(question, answer, context_chunks)
    hallucination_ms = int((time.time() - t2) * 1000)
    print(f"[Query] Grounded: {is_grounded} | Hallucination check: {hallucination_ms}ms")

    if not is_grounded:
        answer += (
            "\n\n---\n"
            "Note: Some claims in this answer could not be fully verified "
            "against the retrieved data catalog entries."
        )

    # Step 6: Enhanced logging
    chunk_ids = [_chunk_id(c) for c in context_chunks]
    log_event({
        "type": "query",
        "query_id": query_id,
        "question": question,
        "model_used": model_used,
        "chunks_retrieved": len(context_chunks),
        "chunk_ids": chunk_ids,
        "top_scores": [round(s, 3) for s in top_scores],
        "top_collections": [c["collection"] for c in context_chunks[:3]],
        "keyword_matches": keyword_count,
        "feedback_boosted": boosted_count,
        "retrieval_quality": quality,
        "citations_valid": citations_valid,
        "grounded": is_grounded,
        "grounding_details": grounding_details if not is_grounded else None,
        "retrieval_ms": retrieval_ms,
        "generation_ms": generation_ms,
        "hallucination_check_ms": hallucination_ms,
        "total_ms": retrieval_ms + generation_ms + hallucination_ms,
        "answer_length": len(answer),
    })

    return query_id, answer


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        q = " ".join(sys.argv[1:])
    else:
        q = "What does col_x1a mean in the silver layer?"
    _, result = query(q)
    print(result)
