from typing import List, Dict

def truncate(s: str, max_chars: int) -> str:
    return s if len(s) <= max_chars else s[:max_chars] + " …"

def build_api_cards(docs: List[Dict], max_examples_per_doc: int = 2,
                    max_chars_per_doc: int = 1400, max_total_chars: int = 6000) -> str:
    parts = []
    total = 0
    for d in docs:
        title = f"{d['object']}.{d['method']}  (ID: {d['id']})"
        sigs  = "; ".join([", ".join(v["args"]) + " -> " + v["returns"] for v in d.get("signature_variants", [])])
        exs   = d.get("minimal_examples", [])[:max_examples_per_doc]
        card  = f"[{title}]\nSignaturer: {sigs}\nEksempler:\n" + "\n---\n".join(exs)
        card  = truncate(card, max_chars_per_doc)
        if total + len(card) > max_total_chars:
            break
        parts.append(card)
        total += len(card)
    return "\n\n".join(parts)
