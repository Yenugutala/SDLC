"""CLI interface to query the data catalog using RAG."""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from rag.query_engine import query


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
    answer = query(question)
    print(f"\n{'=' * 60}")
    print(f"Q: {question}")
    print(f"{'=' * 60}")
    print(f"\n{answer}\n")


if __name__ == "__main__":
    main()
