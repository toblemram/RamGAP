"""Extract all formulas and values from the Excel BEREGNING sheet."""
import zipfile
import xml.etree.ElementTree as ET
import json

path = "Dimensjonering av tørrmurer iht V220_rev 1.xltm"
ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"

with zipfile.ZipFile(path) as zf:
    wb = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rid_map = {r.attrib["Id"]: r.attrib["Target"] for r in rels}

    sheet_target = None
    for s in wb.findall(f".//{{{ns}}}sheet"):
        if s.attrib["name"].upper() == "BEREGNING":
            rid = s.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
            sheet_target = "xl/" + rid_map[rid]
            break

    print(f"Sheet: {sheet_target}")
    root = ET.fromstring(zf.read(sheet_target))

    shared = []
    if "xl/sharedStrings.xml" in zf.namelist():
        sst = ET.fromstring(zf.read("xl/sharedStrings.xml"))
        for si in sst:
            texts = [t.text or "" for t in si.iter(f"{{{ns}}}t")]
            shared.append("".join(texts))

    cells = {}
    for c in root.findall(f".//{{{ns}}}c"):
        ref = c.attrib["r"]
        ctype = c.attrib.get("t", "")
        formula_el = c.find(f"{{{ns}}}f")
        value_el = c.find(f"{{{ns}}}v")

        entry = {}
        if formula_el is not None and formula_el.text:
            entry["formula"] = formula_el.text
        if value_el is not None:
            if ctype == "s":
                entry["value"] = shared[int(value_el.text)]
            else:
                entry["value"] = value_el.text
        if ctype:
            entry["type"] = ctype
        if entry:
            cells[ref] = entry

    import re
    def cell_sort_key(ref):
        m = re.match(r"([A-Z]+)(\d+)", ref)
        if m:
            return (m.group(1), int(m.group(2)))
        return (ref, 0)

    for ref in sorted(cells.keys(), key=cell_sort_key):
        print(f"{ref}: {json.dumps(cells[ref], ensure_ascii=False)}")
