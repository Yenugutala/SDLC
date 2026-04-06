"""RAGAS-style evaluation suite for the RAG pipeline.

Metrics computed per question:
  - Context Precision: relevant chunks / total chunks (LLM-judged)
  - Context Recall: expected collections represented / total expected
  - Faithfulness: is the answer grounded in retrieved context?
  - Answer Relevancy: LLM score (0-1) of how well the answer addresses the question

Usage:
    python3 -m rag.evaluation              # full eval (all questions)
    python3 -m rag.evaluation --quick      # quick eval (5 key questions)
"""

import json
import os
import sys
import time

import anthropic

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from rag.query_engine import (
    search_vectorstore,
    ask_claude,
    check_hallucination,
    verify_citations,
    route_query,
)

PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
RESULTS_FILE = os.path.join(PROJECT_DIR, "profiling_output", "eval_results.json")
EVAL_FILE = os.path.join(PROJECT_DIR, "profiling_output", "eval_test_cases.json")

# Subset indices for --quick mode
QUICK_INDICES = [0, 3, 6, 8, 12]


def load_test_cases():
    """Load evaluation test cases from external JSON file.

    SMEs maintain test cases in profiling_output/eval_test_cases.json
    without needing to edit Python code.
    """
    with open(EVAL_FILE) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Metric functions
# ---------------------------------------------------------------------------

def eval_context_precision(question, ground_truth, chunks):
    """LLM-judged: what fraction of retrieved chunks are relevant to the question?"""
    if not chunks:
        return 0.0

    client = anthropic.Anthropic()
    judgments = []

    for i, chunk in enumerate(chunks):
        result = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{
                "role": "user",
                "content": (
                    f"Question: {question}\n"
                    f"Expected answer: {ground_truth}\n"
                    f"Retrieved chunk: {chunk['document'][:500]}\n\n"
                    "Is this chunk relevant to answering the question? "
                    "Respond with exactly YES or NO."
                ),
            }],
        )
        answer = result.content[0].text.strip().upper()
        judgments.append(1 if "YES" in answer else 0)

    return sum(judgments) / len(judgments)


def eval_context_recall(chunks, expected_collections):
    """What fraction of expected collections are represented in retrieved chunks?"""
    if not expected_collections:
        return 1.0
    retrieved_collections = {c["collection"] for c in chunks}
    found = sum(1 for ec in expected_collections if ec in retrieved_collections)
    return found / len(expected_collections)


def eval_faithfulness(question, answer, chunks):
    """Is the answer grounded in the retrieved context? Returns 0.0 or 1.0."""
    if not chunks or not answer:
        return 0.0
    is_grounded, _ = check_hallucination(question, answer, chunks)
    return 1.0 if is_grounded else 0.0


def eval_answer_relevancy(question, answer, ground_truth):
    """LLM-judged: how well does the answer address the question? Returns 0.0-1.0."""
    if not answer:
        return 0.0

    client = anthropic.Anthropic()
    result = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=50,
        messages=[{
            "role": "user",
            "content": (
                f"Question: {question}\n"
                f"Expected answer: {ground_truth}\n"
                f"Actual answer: {answer[:1000]}\n\n"
                "Rate how well the actual answer addresses the question on a scale of 0.0 to 1.0. "
                "Consider: does it cover the key facts in the expected answer? "
                "Respond with ONLY a decimal number between 0.0 and 1.0."
            ),
        }],
    )
    try:
        score = float(result.content[0].text.strip())
        return max(0.0, min(1.0, score))
    except ValueError:
        return 0.5  # default if parsing fails


# ---------------------------------------------------------------------------
# Main evaluation runner
# ---------------------------------------------------------------------------

def run_evaluation(dataset, verbose=True):
    """Run the full RAGAS-style evaluation on the given dataset."""
    results = []
    totals = {"precision": 0, "recall": 0, "faithfulness": 0, "relevancy": 0}

    for i, test_case in enumerate(dataset):
        question = test_case["question"]
        ground_truth = test_case["ground_truth"]
        expected_collections = test_case["expected_collections"]

        if verbose:
            print(f"\n[{i+1}/{len(dataset)}] {question}")

        t0 = time.time()

        # Retrieve
        chunks = search_vectorstore(question)

        # Generate
        model_used, answer = ask_claude(question, chunks)

        # Compute metrics
        precision = eval_context_precision(question, ground_truth, chunks)
        recall = eval_context_recall(chunks, expected_collections)
        faithfulness = eval_faithfulness(question, answer, chunks)
        relevancy = eval_answer_relevancy(question, answer, ground_truth)

        elapsed = time.time() - t0

        # Citation check
        citations_ok, _ = verify_citations(answer, len(chunks))
        model_routed = route_query(question)

        result = {
            "question": question,
            "domain": test_case.get("domain", "unknown"),
            "ground_truth": ground_truth,
            "context_precision": round(precision, 2),
            "context_recall": round(recall, 2),
            "faithfulness": round(faithfulness, 2),
            "answer_relevancy": round(relevancy, 2),
            "chunks_retrieved": len(chunks),
            "collections_hit": list({c["collection"] for c in chunks}),
            "expected_collections": expected_collections,
            "citations_valid": citations_ok,
            "model_routed": model_routed,
            "model_used": model_used,
            "elapsed_s": round(elapsed, 1),
            "answer_preview": answer[:200],
        }
        results.append(result)

        totals["precision"] += precision
        totals["recall"] += recall
        totals["faithfulness"] += faithfulness
        totals["relevancy"] += relevancy

        if verbose:
            print(f"   Prec={precision:.2f}  Recall={recall:.2f}  "
                  f"Faith={faithfulness:.2f}  Relev={relevancy:.2f}  "
                  f"({elapsed:.1f}s, {model_used})")

    n = len(dataset)
    averages = {k: round(v / n, 2) for k, v in totals.items()} if n else totals

    return results, averages


def print_report(results, averages):
    """Print the RAGAS-style evaluation report table."""
    print(f"\n{'=' * 78}")
    print("RAGAS Evaluation Report")
    print(f"{'=' * 78}")
    print(f"{'Question':<42} {'Prec':>6} {'Recall':>7} {'Faith':>6} {'Relev':>6}")
    print(f"{'-' * 78}")

    for r in results:
        q = r["question"]
        if len(q) > 40:
            q = q[:37] + "..."
        print(f"{q:<42} {r['context_precision']:>6.2f} {r['context_recall']:>7.2f} "
              f"{r['faithfulness']:>6.2f} {r['answer_relevancy']:>6.2f}")

    print(f"{'-' * 78}")
    print(f"{'AVERAGE':<42} {averages['precision']:>6.2f} {averages['recall']:>7.2f} "
          f"{averages['faithfulness']:>6.2f} {averages['relevancy']:>6.2f}")
    print(f"{'=' * 78}")

    # Domain breakdown
    domains = {}
    for r in results:
        d = r.get("domain", "unknown")
        if d not in domains:
            domains[d] = {"precision": [], "recall": [], "faithfulness": [], "relevancy": []}
        domains[d]["precision"].append(r["context_precision"])
        domains[d]["recall"].append(r["context_recall"])
        domains[d]["faithfulness"].append(r["faithfulness"])
        domains[d]["relevancy"].append(r["answer_relevancy"])

    print(f"\n{'Domain Breakdown'}")
    print(f"{'-' * 78}")
    print(f"{'Domain':<20} {'Count':>5} {'Prec':>6} {'Recall':>7} {'Faith':>6} {'Relev':>6}")
    print(f"{'-' * 78}")
    for domain, metrics in sorted(domains.items()):
        n = len(metrics["precision"])
        avg_p = sum(metrics["precision"]) / n
        avg_r = sum(metrics["recall"]) / n
        avg_f = sum(metrics["faithfulness"]) / n
        avg_v = sum(metrics["relevancy"]) / n
        print(f"{domain:<20} {n:>5} {avg_p:>6.2f} {avg_r:>7.2f} {avg_f:>6.2f} {avg_v:>6.2f}")
    print(f"{'=' * 78}")


def save_results(results, averages):
    """Save detailed results to JSON for tracking over time."""
    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "num_questions": len(results),
        "averages": averages,
        "results": results,
    }
    os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)
    with open(RESULTS_FILE, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nDetailed results saved to {RESULTS_FILE}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    from dotenv import load_dotenv
    load_dotenv()

    quick = "--quick" in sys.argv
    all_cases = load_test_cases()

    if quick:
        dataset = [all_cases[i] for i in QUICK_INDICES if i < len(all_cases)]
        print(f"Running QUICK evaluation ({len(dataset)} questions)...\n")
    else:
        dataset = all_cases
        print(f"Running FULL evaluation ({len(dataset)} questions)...\n")

    results, averages = run_evaluation(dataset)
    print_report(results, averages)
    save_results(results, averages)


if __name__ == "__main__":
    main()
