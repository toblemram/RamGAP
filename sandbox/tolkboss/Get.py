import json

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

docs = notebook_to_text("contents_2d.ipynb")
print("Antall dokumenter:", len(docs))
print("Eksempel:", docs[0][:300])
