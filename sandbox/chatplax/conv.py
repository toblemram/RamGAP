import json, faiss, numpy as np, pickle
from openai import OpenAI

import os
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

# === Notebook til tekst/chunks (som vi hadde før) ===
def notebook_to_text(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    docs = []
    for cell in data.get("cells", []):
        if cell.get("cell_type") in ["markdown", "code"]:
            text = "".join(cell.get("source", []))
            if text.strip():
                docs.append(text.strip())
    return docs

def chunk_text(texts, chunk_size=200, overlap=50):
    chunks = []
    for text in texts:
        words = text.split()
        for i in range(0, len(words), chunk_size - overlap):
            chunks.append(" ".join(words[i:i+chunk_size]))
    return chunks

def embed_texts(texts, client, model="text-embedding-3-small"):
    out = []
    for t in texts:
        emb = client.embeddings.create(model=model, input=t).data[0].embedding
        out.append(emb)
    return np.array(out).astype("float32")

# === Kjør en gang ===
docs = notebook_to_text("contents_2d.ipynb")
chunks = chunk_text(docs, 200)
embeddings = embed_texts(chunks, client)

dim = embeddings.shape[1]
index = faiss.IndexFlatL2(dim)
index.add(embeddings)

# lagre til disk
faiss.write_index(index, "plaxis.index")
with open("plaxis_texts.pkl", "wb") as f:
    pickle.dump(chunks, f)

print("✅ Notebook prosessert og lagret!")
