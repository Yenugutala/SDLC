"""CLI interface to query the data catalog using RAG.

Usage:
    python ask.py "your question"            # non-streaming (default)
    python ask.py --stream "your question"   # streaming (tokens appear as generated)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from rag.query_engine import query, record_feedback, _chunk_id


def main():
    args = sys.argv[1:]

    if not args:
        print("Usage: python ask.py [--stream] \"<your question>\"")
        print()
        print("Options:")
        print("  --stream    Stream the response token by token")
        print()
        print("Example queries:")
        print('  python ask.py "What does col_x1a mean in silver_tbl_a1?"')
        print('  python ask.py "Show me the lineage of patient_id"')
        print('  python ask.py --stream "How is Total Revenue calculated in PBI?"')
        print('  python ask.py "How are patients and visits related?"')
        sys.exit(1)

    stream = False
    if "--stream" in args:
        stream = True
        args.remove("--stream")

    question = " ".join(args)

    if stream:
        print(f"\n{'=' * 60}")
        print(f"Q: {question}")
        print(f"{'=' * 60}\n")
        query_id, answer = query(question, stream=True)
    else:
        query_id, answer = query(question)
        print(f"\n{'=' * 60}")
        print(f"Q: {question}")
        print(f"{'=' * 60}")
        print(f"\n{answer}\n")

    # Collect user feedback
    try:
        feedback = input("\nWas this answer helpful? (y/n/skip): ").strip().lower()
        if feedback in ("y", "n"):
            from rag.query_engine import search_vectorstore
            chunks = search_vectorstore(question)
            chunk_ids = [_chunk_id(c) for c in chunks]
            record_feedback(query_id, question, chunk_ids, helpful=(feedback == "y"))
            print("[Feedback] Thank you! Your feedback helps improve future answers.")
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()
