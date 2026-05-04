"""
BEAM dataset inspection utility for Kyros benchmarks.

This script inspects the structure of the BEAM (Benchmark for Evaluating
AI Memory) dataset used for benchmarking the Kyros memory system.

Requires: datasets library (pip install datasets)
"""

import json
import sys


def inspect_beam_dataset(subset: str = "1M") -> None:
    """
    Inspect BEAM dataset structure.

    Args:
        subset: Dataset subset to inspect (default: "1M")
    """
    try:
        from datasets import load_dataset
    except ImportError:
        print("Error: datasets library not installed")
        print("Install with: pip install datasets")
        sys.exit(1)

    print(f"Loading BEAM dataset (subset: {subset})...")
    print("=" * 80)

    try:
        ds = load_dataset("Mohammadta/BEAM")

        if subset not in ds:
            print(f"Error: Subset '{subset}' not found in dataset")
            print(f"Available subsets: {list(ds.keys())}")
            sys.exit(1)

        row = ds[subset][0]

        # Inspect probing_questions
        print("\n=== Probing Questions ===")
        pq = row["probing_questions"]
        if isinstance(pq, str):
            pq = json.loads(pq)

        print(f"Keys: {list(pq.keys())}")
        for qtype, items in pq.items():
            print(f"\n  [{qtype}] ({len(items)} items)")
            if items:
                sample = json.dumps(items[0], indent=4)[:400]
                print(f"  Sample:\n{sample}")

        # Inspect user_questions
        print("\n\n=== User Questions ===")
        uq = row["user_questions"]
        print(f"Type: {type(uq).__name__}")

        if isinstance(uq, list) and uq:
            if isinstance(uq[0], dict):
                print(f"First item keys: {list(uq[0].keys())}")
            else:
                print(f"First item type: {type(uq[0])}")

            sample = json.dumps(uq[0], indent=2)[:400]
            print(f"Sample:\n{sample}")

        # Inspect chat structure
        print("\n\n=== Chat Structure ===")
        chat = row["chat"]
        print(f"Type: {type(chat).__name__}, Length: {len(chat)}")

        if chat:
            batch = chat[0]
            print(f"Batch type: {type(batch).__name__}, Length: {len(batch)}")

            if batch:
                turn = batch[0]
                if isinstance(turn, dict):
                    print(f"Turn keys: {list(turn.keys())}")
                    sample = json.dumps(turn, indent=2)[:300]
                else:
                    sample = str(turn)[:300]

                print(f"Turn sample:\n{sample}")

        print("\n" + "=" * 80)
        print("Inspection complete!")

    except Exception as e:
        print(f"Error loading dataset: {e}")
        sys.exit(1)


def main():
    """Main entry point for BEAM dataset inspection."""
    import argparse

    parser = argparse.ArgumentParser(description="Inspect BEAM benchmark dataset structure")
    parser.add_argument(
        "--subset", type=str, default="1M", help="Dataset subset to inspect (default: 1M)"
    )

    args = parser.parse_args()
    inspect_beam_dataset(args.subset)


if __name__ == "__main__":
    main()
