"""
llm_ocr.py
----------
OCR using GPT-4o vision via OpenRouter.
Converts each PDF page to an image, extracts text via LLM, then chunks
and stores the results in a persistent ChromaDB vector store.

Advanced RAG techniques used:
    1. Contextual retrieval  — LLM generates a 1-2 sentence context that
                               situates each chunk within the full document
                               before embedding. Improves retrieval precision.
    2. Parent-child chunking — full page stored as parent; smaller chunks
                               stored as children with a parentId pointer.
                               At query time the parent can be fetched for
                               full context even when a child chunk matched.
    3. Persistent ChromaDB   — data survives sessions (OCR is expensive;
                               re-running it every session is wasteful).
    4. Overlapping chunks    — 1280-char window, 160-char overlap so context
                               is not lost at chunk boundaries.
"""

import os
import sys
import base64
from io import BytesIO
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
from pdf2image import convert_from_path
from dotenv import load_dotenv

# Allow importing rag.chunker from the project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag.chunker import chunkText

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PDF_PATH   = Path("dps/samples/DPS - UCM .pdf")
API_KEY    = os.environ["OPENROUTER_API_KEY"]
MODEL      = "openai/gpt-4o"

# Persistent ChromaDB stored inside the ocr/ folder
CHROMA_PATH = Path(__file__).parent / "chroma_db"

client = OpenAI(
    api_key=API_KEY,
    base_url="https://openrouter.ai/api/v1",
)


# ---------------------------------------------------------------------------
# Vector store (persistent)
# ---------------------------------------------------------------------------

def get_vector_store():
    """
    Return a persistent ChromaDB collection for OCR PDF documents.

    Uses all-MiniLM-L6-v2 (384-dim) for embeddings — same model as the
    main KG vector store so similarity scores are comparable.
    Persistent client writes to ocr/chroma_db/ on disk.
    """
    db_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    return db_client.get_or_create_collection(
        name="ocr_pdf_documents",
        embedding_function=embed_fn,
    )


# ---------------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------------

def image_to_base64(image) -> str:
    """Encode a PIL image as a base64 PNG string for the vision API."""
    buf = BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def ocr_page(image, page_num: int) -> str:
    """
    Send a single page image to GPT-4o and return extracted markdown text.

    The prompt instructs the model to preserve table structure, headings,
    and bullet points so downstream chunking and retrieval stay meaningful.
    """
    print(f"  Extracting page {page_num}...")
    b64 = image_to_base64(image)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"}
                },
                {
                    "type": "text",
                    "text": (
                        "Extract all text from this document page. "
                        "Preserve tables as markdown. "
                        "Preserve headings, bullet points, and structure. "
                        "Return only the extracted content, no commentary."
                    )
                }
            ]
        }],
        temperature=0.0,
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Contextual retrieval
# ---------------------------------------------------------------------------

def generate_chunk_context(full_page_text: str, chunk: str, page_num: int, filename: str) -> str:
    """
    Contextual retrieval (Anthropic technique):
    Ask the LLM to write a 1-2 sentence context that situates this chunk
    within the broader page/document before it is embedded.

    Why this helps:
        A chunk like "The retention period is 7 years." is ambiguous in
        isolation. With context — "This chunk is from the GDPR compliance
        section of the DPS UCM document (page 4)." — the embedding captures
        the domain intent, improving retrieval precision.

    Args:
        full_page_text: Full OCR text of the page (used as surrounding context).
        chunk:          The specific chunk being embedded.
        page_num:       Page number for the context prompt.
        filename:       Source filename for the context prompt.

    Returns:
        A short context string to prepend to the chunk before embedding.
    """
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": (
                f"Here is a page (page {page_num}) from the document '{filename}':\n\n"
                f"<document>\n{full_page_text[:2000]}\n</document>\n\n"
                f"Here is a specific excerpt from that page:\n\n"
                f"<chunk>\n{chunk}\n</chunk>\n\n"
                "Write 1-2 sentences that situate this excerpt within the document "
                "(what section it belongs to, what it is about). "
                "Be concise and factual. Return only the context, no preamble."
            )
        }],
        temperature=0.0,
        max_tokens=80,
    )
    return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Chunking + vector store ingestion
# ---------------------------------------------------------------------------

def store_pages_in_vectordb(
    pages: list[tuple[int, str]],
    filename: str,
    use_contextual_retrieval: bool = True,
) -> None:
    """
    Chunk and store OCR-extracted pages in ChromaDB.

    Strategy:
        Parent-child chunking:
            - Full page text → stored as parent (chunk_type="parent")
            - Overlapping sub-chunks → stored as children (chunk_type="child")
              Each child carries a parentId pointer so the retriever can
              fetch the full page for re-ranking or context injection.

        Contextual retrieval (optional, adds LLM calls per chunk):
            - For each child chunk, the LLM generates a short context string
              which is prepended before embedding. This anchors the chunk's
              meaning in the document structure.

    Args:
        pages:                     List of (page_num, extracted_text) tuples.
        filename:                  Source PDF filename (used in doc IDs + metadata).
        use_contextual_retrieval:  Set False to skip context generation (faster, cheaper).
    """
    collection = get_vector_store()
    stem = Path(filename).stem.replace(" ", "_")

    print(f"\nStoring {len(pages)} page(s) in ChromaDB...")

    for page_num, page_text in pages:
        parent_id = f"pdf_{stem}_page_{page_num}"

        # --- Parent: full page text ---
        # Stored so retriever can return full-page context when a child chunk matches.
        collection.upsert(
            ids=[parent_id],
            documents=[page_text],
            metadatas=[{
                "source":     "pdf",
                "filename":   filename,
                "page_num":   str(page_num),
                "chunk_type": "parent",
            }]
        )

        # --- Children: overlapping sub-chunks ---
        chunks = chunkText(page_text)

        # Single-chunk page — no children needed (parent IS the chunk)
        if len(chunks) == 1:
            continue

        print(f"  Page {page_num}: {len(chunks)} chunks", end="")

        for i, chunk in enumerate(chunks):
            child_id = f"{parent_id}_chunk_{i}"

            if use_contextual_retrieval:
                # Prepend LLM-generated context before embedding
                context = generate_chunk_context(page_text, chunk, page_num, filename)
                text_to_embed = f"{context}\n\n{chunk}"
                print(".", end="", flush=True)
            else:
                text_to_embed = chunk

            collection.upsert(
                ids=[child_id],
                documents=[text_to_embed],
                metadatas=[{
                    "source":       "pdf",
                    "filename":     filename,
                    "page_num":     str(page_num),
                    "chunk_type":   "child",
                    "chunk_index":  str(i),
                    "total_chunks": str(len(chunks)),
                    "parent_id":    parent_id,
                    "raw_chunk":    chunk,          # original text without context prefix
                }]
            )

        print()  # newline after dots

    total = collection.count()
    print(f"\nDone. Total documents in ocr_pdf_documents collection: {total}")


# ---------------------------------------------------------------------------
# Search helper
# ---------------------------------------------------------------------------

def search_pdf(query: str, k: int = 5, page_num: int = None) -> None:
    """
    Semantic search over stored PDF chunks.

    Args:
        query:    Natural language query.
        k:        Number of results to return.
        page_num: Optional — filter results to a specific page.
    """
    collection = get_vector_store()
    where = {"page_num": str(page_num)} if page_num else None

    results = collection.query(
        query_texts=[query],
        n_results=k,
        where=where,
    )

    print(f"\nSearch: '{query}'\n{'=' * 60}")
    for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0]), 1):
        print(f"\n[{i}] Page {meta.get('page_num')} | {meta.get('chunk_type')} | {meta.get('filename')}")
        print(f"    {doc[:300]}...")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(store: bool = True, contextual: bool = False):
    """
    Run OCR on the PDF and optionally store results in ChromaDB.

    Args:
        store:      Whether to store extracted text in ChromaDB (default True).
        contextual: Whether to use contextual retrieval (adds LLM calls per chunk).
                    Defaults to False to avoid extra API cost unless explicitly requested.
    """
    print(f"Loading PDF: {PDF_PATH}\n")
    images = convert_from_path(str(PDF_PATH), dpi=200)
    print(f"Found {len(images)} page(s). Sending to GPT-4o via OpenRouter...\n")

    pages = []
    for i, image in enumerate(images, 1):
        text = ocr_page(image, i)
        pages.append((i, text))
        print(f"{'=' * 60}")
        print(f"PAGE {i}")
        print(f"{'=' * 60}")
        print(text)
        print()

    if store:
        store_pages_in_vectordb(
            pages,
            filename=PDF_PATH.name,
            use_contextual_retrieval=contextual,
        )


if __name__ == "__main__":
    # Set contextual=True to enable LLM context generation per chunk (costs extra API calls)
    run(store=True, contextual=False)
