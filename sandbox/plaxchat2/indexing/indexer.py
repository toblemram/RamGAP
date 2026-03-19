import os, json, sqlite3, numpy as np, re, unicodedata
from dotenv import load_dotenv
from openai import OpenAI
import faiss
from indexing.utils import list_json_files, load_json, safe_concat

load_dotenv()
DATA_DIR   = os.getenv("DATA_DIR", "plaxis_knowledge")
DB_FILE    = os.getenv("DB_FILE", "plaxis.db")
IDX_SHORT  = os.getenv("IDX_SHORT", "faiss_short.index")
IDX_FULL   = os.getenv("IDX_FULL",  "faiss_full.index")
IDS_FILE   = os.getenv("IDS_FILE",  "doc_ids.json")
EMB_MODEL  = os.getenv("EMBED_MODEL", "text-embedding-3-large")

client = OpenAI()

def normalize_text(s: str) -> str:
    """Fjerner diakritikk + rydder whitespace."""
    if not s:
        return ""
    s = ''.join(
        c for c in unicodedata.normalize("NFKD", s)
        if not unicodedata.combining(c)
    )
    return re.sub(r"\s+", " ", s).strip()

def embed(text: str) -> np.ndarray:
    """Lager normalisert embedding (cosine/IP)."""
    text = normalize_text(text)
    vec = client.embeddings.create(model=EMB_MODEL, input=text).data[0].embedding
    x = np.array(vec, dtype="float32")
    x = x / np.linalg.norm(x)
    return x

def build_index():
    """Bygger SQLite + FAISS indekser fra alle JSON-dokumenter i DATA_DIR."""
    conn = sqlite3.connect(DB_FILE)
    cur  = conn.cursor()

    # Nuke & create FTS table
    cur.execute("DROP TABLE IF EXISTS docs_fts")
    cur.execute("""
    CREATE VIRTUAL TABLE docs_fts USING fts5(
      id, title, object, method, aliases, content,
      tokenize = 'unicode61'
    )
    """)

    # FAISS
    DIM = 3072  # text-embedding-3-large
    faiss_short = faiss.IndexFlatIP(DIM)
    faiss_full  = faiss.IndexFlatIP(DIM)
    doc_ids = []

    for path in list_json_files(DATA_DIR):
        doc = load_json(path)

        doc_id   = doc["id"]
        title    = f"{doc['object']}.{doc['method']}"
        aliases  = " ".join(doc.get("aliases", []))
        synopsis = doc.get("synopsis", "")

        # Short & full text
        short_text = safe_concat(title, synopsis, aliases)
        signatures = " | ".join(
            [", ".join(v["args"]) + " -> " + v["returns"] for v in doc.get("signature_variants", [])]
        )
        examples   = " \n ".join(doc.get("minimal_examples", []))
        full_text  = safe_concat(short_text, signatures, examples)

        # Embeddings
        e_short = embed(short_text)
        e_full  = embed(full_text)
        faiss_short.add(e_short.reshape(1, -1))
        faiss_full.add(e_full.reshape(1, -1))

        doc_ids.append(doc_id)

        # SQLite
        cur.execute(
            "INSERT INTO docs_fts (id, title, object, method, aliases, content) VALUES (?, ?, ?, ?, ?, ?)",
            (
                doc_id,
                normalize_text(title),
                normalize_text(doc["object"]),
                normalize_text(doc["method"]),
                normalize_text(aliases),
                normalize_text(synopsis + " " + signatures + " " + examples),
            )
        )

    conn.commit()

    # Lagre FAISS + ID-liste
    faiss.write_index(faiss_short, IDX_SHORT)
    faiss.write_index(faiss_full,  IDX_FULL)
    with open(IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(doc_ids, f, ensure_ascii=False, indent=2)

    print(f"✅ Indeksering ferdig. {len(doc_ids)} dokumenter.")

if __name__ == "__main__":
    build_index()
