"""
Dataset inspection utility for Kyros benchmarks.

This script inspects the structure of MSC and LoCoMo datasets
used for benchmarking the Kyros memory system.
"""

import json
import sys
from pathlib import Path


def inspect_msc_dataset(filepath: str) -> None:
    """
    Inspect MSC (Multi-Session Chat) dataset structure.

    Args:
        filepath: Path to the MSC JSON file
    """
    print(f"Inspecting MSC dataset: {filepath}")
    print("=" * 80)

    try:
        with open(filepath, encoding="utf-8") as f:
            msc = json.load(f)

        # Show structure of first item
        if "train" in msc and len(msc["train"]) > 0:
            item = msc["train"][0]
            print("MSC train[0] keys:", list(item.keys()))
            print("\nFull item (first 1200 chars):")
            print(json.dumps(item, indent=2)[:1200])

        # Show dataset sizes
        print(f"\n\nDataset sizes:")
        print(f"  Total train: {len(msc.get('train', []))}")
        print(f"  Total valid: {len(msc.get('valid', []))}")
        print(f"  Total test: {len(msc.get('test', []))}")

    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}")
        sys.exit(1)


def inspect_locomo_dataset(filepath: str) -> None:
    """
    Inspect LoCoMo (Long Context Memory) dataset structure.

    Args:
        filepath: Path to the LoCoMo JSON file
    """
    print(f"\n\nInspecting LoCoMo dataset: {filepath}")
    print("=" * 80)

    try:
        with open(filepath, encoding="utf-8") as f:
            locomo = json.load(f)

        # Show QA category distribution
        print("\nLoCoMo QA category distribution:")
        for item in locomo:
            cats = {}
            for q in item["qa"]:
                c = q["category"]
                cats[c] = cats.get(c, 0) + 1
            sid = item["sample_id"]
            print(f"  {sid}: {cats}")

        # Show evidence format examples
        if len(locomo) > 0 and "qa" in locomo[0]:
            print("\nLoCoMo evidence examples (first 5 questions):")
            for q in locomo[0]["qa"][:5]:
                print(f"  Q: {q['question'][:60]}...")
                print(f"  A: {q['answer']}")
                print(f"  Evidence: {q['evidence']}")
                print(f"  Category: {q['category']}")
                print()

    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}")
        sys.exit(1)


def main():
    """Main entry point for dataset inspection."""
    import argparse

    parser = argparse.ArgumentParser(description="Inspect MSC and LoCoMo benchmark datasets")
    parser.add_argument("--msc", type=str, help="Path to MSC dataset JSON file")
    parser.add_argument("--locomo", type=str, help="Path to LoCoMo dataset JSON file")

    args = parser.parse_args()

    if not args.msc and not args.locomo:
        parser.print_help()
        print("\nError: Please specify at least one dataset to inspect")
        sys.exit(1)

    if args.msc:
        inspect_msc_dataset(args.msc)

    if args.locomo:
        inspect_locomo_dataset(args.locomo)


if __name__ == "__main__":
    main()
