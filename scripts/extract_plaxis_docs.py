"""
Extract ALL Plaxis 2D command documentation from Jupyter notebooks.
Outputs a single comprehensive reference file.
"""
import json
import urllib.request
import re
import sys
import time

TOKEN = "441d43246a09f4332bd5153dec95df394f7635a4394eee72"
BASE = "http://localhost:8889"

def fetch_notebook(path: str) -> dict | None:
    """Fetch a notebook's JSON via the Jupyter API."""
    url = f"{BASE}/api/contents/{path}?token={TOKEN}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            return data.get("content", {})
    except Exception as e:
        print(f"  WARN: Could not fetch {path}: {e}", file=sys.stderr)
        return None


def extract_cells(nb: dict) -> list[dict]:
    """Extract all cells from a notebook."""
    cells = nb.get("cells", [])
    result = []
    for cell in cells:
        ct = cell.get("cell_type", "")
        source = "".join(cell.get("source", []))
        if source.strip():
            result.append({"type": ct, "source": source.strip()})
    return result


def parse_contents() -> dict:
    """Parse the contents_2d.ipynb to extract all notebook links."""
    nb = fetch_notebook("contents_2d.ipynb")
    if not nb:
        print("ERROR: Could not fetch contents_2d.ipynb", file=sys.stderr)
        sys.exit(1)
    
    input_notebooks = []
    output_notebooks = []
    
    cells = nb.get("cells", [])
    current_section = None
    
    for cell in cells:
        source = "".join(cell.get("source", []))
        if "### Input" in source:
            current_section = "input"
        elif "### Output" in source:
            current_section = "output"
        
        # Extract notebook links
        links = re.findall(r'\[([^\]]+)\]\(([^)]+\.ipynb)\)', source)
        for name, path in links:
            if current_section == "input":
                input_notebooks.append((name, path))
            elif current_section == "output":
                output_notebooks.append((name, path))
    
    return {"input": input_notebooks, "output": output_notebooks}


def format_cell_content(cells: list[dict]) -> str:
    """Format notebook cells into readable documentation."""
    parts = []
    for cell in cells:
        if cell["type"] == "markdown":
            parts.append(cell["source"])
        elif cell["type"] == "code":
            parts.append(f"```python\n{cell['source']}\n```")
    return "\n\n".join(parts)


def main():
    print("Parsing contents_2d.ipynb...", file=sys.stderr)
    toc = parse_contents()
    
    total = len(toc["input"]) + len(toc["output"])
    print(f"Found {len(toc['input'])} input commands, {len(toc['output'])} output commands ({total} total)", file=sys.stderr)
    
    output_lines = []
    output_lines.append("# PLAXIS 2D Python Scripting - Complete Command Reference")
    output_lines.append("")
    output_lines.append("This document contains ALL Plaxis 2D Python scripting commands")
    output_lines.append("extracted from the official Jupyter reference notebooks.")
    output_lines.append("")
    output_lines.append("## Connection Setup")
    output_lines.append("")
    output_lines.append("```python")
    output_lines.append("from plxscripting.easy import new_server")
    output_lines.append("# Input server (for building/modifying models)")
    output_lines.append("s_i, g_i = new_server('localhost', 10000, password='your_password')")
    output_lines.append("# Output server (for extracting results)")
    output_lines.append("s_o, g_o = new_server('localhost', 10001, password='your_password')")
    output_lines.append("```")
    output_lines.append("")
    
    # Process Input commands
    output_lines.append("---")
    output_lines.append("")
    output_lines.append("# PART 1: INPUT COMMANDS")
    output_lines.append("")
    output_lines.append("Input commands are used with the Input server (g_i, s_i) to")
    output_lines.append("create geometry, assign materials, configure phases, and set up models.")
    output_lines.append("")
    
    count = 0
    for name, path in toc["input"]:
        count += 1
        print(f"  [{count}/{total}] Fetching INPUT: {name} ...", file=sys.stderr)
        nb = fetch_notebook(path)
        if nb:
            cells = extract_cells(nb)
            content = format_cell_content(cells)
            output_lines.append(f"## INPUT: {name}")
            output_lines.append("")
            output_lines.append(content)
            output_lines.append("")
            output_lines.append("---")
            output_lines.append("")
        else:
            output_lines.append(f"## INPUT: {name}")
            output_lines.append("")
            output_lines.append(f"*Documentation not available (notebook: {path})*")
            output_lines.append("")
            output_lines.append("---")
            output_lines.append("")
        # Small delay to not overwhelm the server
        time.sleep(0.05)
    
    # Process Output commands
    output_lines.append("# PART 2: OUTPUT COMMANDS")
    output_lines.append("")
    output_lines.append("Output commands are used with the Output server (g_o, s_o) to")
    output_lines.append("extract results, create plots, and export data after calculation.")
    output_lines.append("")
    
    for name, path in toc["output"]:
        count += 1
        print(f"  [{count}/{total}] Fetching OUTPUT: {name} ...", file=sys.stderr)
        nb = fetch_notebook(path)
        if nb:
            cells = extract_cells(nb)
            content = format_cell_content(cells)
            output_lines.append(f"## OUTPUT: {name}")
            output_lines.append("")
            output_lines.append(content)
            output_lines.append("")
            output_lines.append("---")
            output_lines.append("")
        else:
            output_lines.append(f"## OUTPUT: {name}")
            output_lines.append("")
            output_lines.append(f"*Documentation not available (notebook: {path})*")
            output_lines.append("")
            output_lines.append("---")
            output_lines.append("")
        time.sleep(0.05)
    
    # Write to file with UTF-8 encoding
    out_path = sys.argv[1] if len(sys.argv) > 1 else "plaxis_2d_commands.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    print(f"\nDone! Extracted {count} commands -> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
