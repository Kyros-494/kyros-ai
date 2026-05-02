"""Inspect BEAM dataset structure before writing the benchmark."""
import json

from datasets import load_dataset

print("Loading BEAM...")
ds = load_dataset("Mohammadta/BEAM")
row = ds["1M"][0]

# Inspect probing_questions
pq = row["probing_questions"]
if isinstance(pq, str):
    pq = json.loads(pq)
print("\n=== probing_questions keys:", list(pq.keys()))
for qtype, items in pq.items():
    print(f"\n  [{qtype}] ({len(items)} items)")
    if items:
        print("  Sample:", json.dumps(items[0], indent=4)[:400])

# Inspect user_questions
uq = row["user_questions"]
print("\n=== user_questions type:", type(uq).__name__)
if isinstance(uq, list) and uq:
    print("  First item keys:", list(uq[0].keys()) if isinstance(uq[0], dict) else type(uq[0]))
    print("  Sample:", json.dumps(uq[0], indent=2)[:400])

# Inspect chat structure
chat = row["chat"]
print("\n=== chat type:", type(chat).__name__, "len:", len(chat))
if chat:
    batch = chat[0]
    print("  batch type:", type(batch).__name__, "len:", len(batch))
    if batch:
        turn = batch[0]
        print("  turn keys:", list(turn.keys()) if isinstance(turn, dict) else type(turn))
        print("  turn sample:", json.dumps(turn, indent=2)[:300] if isinstance(turn, dict) else str(turn)[:300])
