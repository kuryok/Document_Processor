import json

path = r"preprocess\output\daea2e7517149932b194525b18db9313b5dd130a1ca8f4c7b15dff997e568551\document.jsonl"
with open(path, encoding="utf-8") as f:
    first = json.loads(f.readline())

print(json.dumps(first, indent=2, ensure_ascii=False))
