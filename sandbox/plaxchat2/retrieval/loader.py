import os, json
from typing import List, Dict

def load_docs_by_ids(ids: list[str], knowledge_dir: str = "plaxis_knowledge") -> List[Dict]:
    idx = {}
    # Pre-build map fra id -> fil (engangskost, eventuelt cache)
    for name in os.listdir(knowledge_dir):
        if name.endswith(".json"):
            path = os.path.join(knowledge_dir, name)
            with open(path, "r", encoding="utf-8") as f:
                doc = json.load(f)
            idx[doc["id"]] = doc
    return [idx[i] for i in ids if i in idx]
