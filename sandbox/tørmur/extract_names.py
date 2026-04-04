"""Extract named ranges from the workbook."""
import zipfile
import xml.etree.ElementTree as ET

path = "Dimensjonering av tørrmurer iht V220_rev 1.xltm"
ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"

with zipfile.ZipFile(path) as zf:
    wb = ET.fromstring(zf.read("xl/workbook.xml"))
    for dn in wb.findall(f".//{{{ns}}}definedName"):
        name = dn.attrib.get("name", "?")
        val = dn.text
        print(f"{name} = {val}")
