"""CLI interface to query the data catalog using RAG."""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from rag.query_engine import query, record_feedback, _chunk_id


def main():
    if len(sys.argv) < 2:
        print("Usage: python ask.py \"<your question>\"")
        print()
        print("Example queries:")
        print('  python ask.py "What does col_x1a mean in silver_tbl_a1?"')
        print('  python ask.py "Show me the lineage of patient_id"')
        print('  python ask.py "What tables exist in the gold layer?"')
        print('  python ask.py "How are patients and visits related?"')
        print('  python ask.py "What is the data type of bill_amount?"')
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    query_id, answer = query(question)
    print(f"\n{'=' * 60}")
    print(f"Q: {question}")
    print(f"{'=' * 60}")
    print(f"\n{answer}\n")

    # Collect user feedback
    try:
        feedback = input("Was this answer helpful? (y/n/skip): ").strip().lower()
        if feedback in ("y", "n"):
            # Re-run search to get chunk_ids for feedback cache
            from rag.query_engine import search_vectorstore
            chunks = search_vectorstore(question)
            chunk_ids = [_chunk_id(c) for c in chunks]
            record_feedback(query_id, question, chunk_ids, helpful=(feedback == "y"))
            print("[Feedback] Thank you! Your feedback helps improve future answers.")
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()
