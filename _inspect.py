import json

# MSC structure
with open(r'C:\Users\jayas\Downloads\msc_personas_all.json', encoding='utf-8') as f:
    msc = json.load(f)

item = msc['train'][0]
print('MSC train[0] keys:', list(item.keys()))
print('Full item:', json.dumps(item, indent=2)[:1200])
print('Total train:', len(msc['train']))
print('Total valid:', len(msc.get('valid', [])))
print('Total test:', len(msc.get('test', [])))

# LoCoMo QA categories
with open(r'C:\Users\jayas\Downloads\locomo10.json', encoding='utf-8') as f:
    locomo = json.load(f)

print('\nLoCoMo QA category distribution:')
for item in locomo:
    cats = {}
    for q in item['qa']:
        c = q['category']
        cats[c] = cats.get(c, 0) + 1
    sid = item['sample_id']
    print(f'  {sid}: {cats}')

# Check evidence format
print('\nLoCoMo evidence examples:')
for q in locomo[0]['qa'][:5]:
    print(f'  Q: {q["question"][:60]}')
    print(f'  A: {q["answer"]}')
    print(f'  Evidence: {q["evidence"]}')
    print(f'  Category: {q["category"]}')
    print()

