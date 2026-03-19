import os, sys, json, sqlite3, numpy as np
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
from openai import OpenAI
import faiss
from indexing.indexer import normalize_text  # gjenbruker normalisering

load_dotenv()

DB_FILE   = os.getenv("DB_FILE", "plaxis.db")
IDX_SHORT = os.getenv("IDX_SHORT", "faiss_short.index")
IDX_FULL  = os.getenv("IDX_FULL",  "faiss_full.index")
IDS_FILE  = os.getenv("IDS_FILE", "doc_ids.json")
EMB_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-large")

client = OpenAI()

# Last inn FAISS + SQLite + ID-liste
faiss_short = faiss.read_index(IDX_SHORT)
faiss_full  = faiss.read_index(IDX_FULL)
with open(IDS_FILE, "r", encoding="utf-8") as f:
    doc_ids = json.load(f)
conn = sqlite3.connect(DB_FILE)

def embed(text: str) -> np.ndarray:
    text = normalize_text(text)
    vec = client.embeddings.create(model=EMB_MODEL, input=text).data[0].embedding
    x = np.array(vec, dtype="float32")
    x = x / np.linalg.norm(x)
    return x

def search(query: str, k=3):
    # --- Embedding-søk (kort + full tekst) ---
    vec = embed(query).reshape(1, -1)

    D1, I1 = faiss_short.search(vec, k)
    D2, I2 = faiss_full.search(vec, k)

    hits = {}
    for i, idx in enumerate(I1[0]):
        if idx < 0: continue
        hits[doc_ids[idx]] = hits.get(doc_ids[idx], 0) + (k - i)

    for i, idx in enumerate(I2[0]):
        if idx < 0: continue
        hits[doc_ids[idx]] = hits.get(doc_ids[idx], 0) + (k - i)

    # --- BM25-søk via FTS5 ---
    cur = conn.cursor()
    cur.execute("SELECT id FROM docs_fts WHERE docs_fts MATCH ? LIMIT ?", (query, k))
    for i, (doc_id,) in enumerate(cur.fetchall()):
        hits[doc_id] = hits.get(doc_id, 0) + (k - i)

    # Rangér kombinerte resultater
    ranked = sorted(hits.items(), key=lambda x: x[1], reverse=True)
    return [doc_id for doc_id, _ in ranked[:k]]

# Test
if __name__ == "__main__":
    q = "legg til added mass på en linje"
    results = search(q, k=3)
    print("Treff:", results)
