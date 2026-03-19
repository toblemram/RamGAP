import os, json, re

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def list_json_files(root: str):
    for name in os.listdir(root):
        if name.endswith(".json"):
            yield os.path.join(root, name)

def normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def safe_concat(*parts):
    return normalize_whitespace(" ".join(p for p in parts if p))
