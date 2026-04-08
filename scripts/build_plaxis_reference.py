"""
Parse the full plaxis_2d_commands.md and create a condensed quick-reference
that removes boilerplate helper functions and organizes by category.
"""
import re
import sys

INPUT_FILE = r"C:\Users\TBLM\RamGAP\RamGAP\docs\plaxis_2d_commands.md"
OUTPUT_FILE = r"C:\Users\TBLM\RamGAP\RamGAP\docs\plaxis_2d_reference.md"

# Boilerplate patterns to strip
BOILERPLATE_PATTERNS = [
    # Full function definitions that repeat in every notebook
    r'The remote scripting server in PLAXIS 2D Input should be activated.*?global environment(?:\s+for the PLAXIS 2D Input application)?.*?(?:from the "g_o" object\.)?',
    r'# Python wrapper commands \[.*?\]',
]

# These helper function bodies appear in almost every notebook
HELPER_FUNCS = [
    "def create_geometry(s_i, g_i):",
    "def simple_test_case(s_i, g_i):",
    "def dynamic_test_case(s_i, g_i):",
    "def embeddedbeam_test_case(s_i, g_i):",
    "def suction_test_case(s_i, g_i):",
]

# Command categories for grouping
CATEGORIES = {
    "Geometry & Drawing": [
        "line", "lineangles", "lineparallel", "linerelative", "linevector",
        "point", "polygon", "rectangle", "polycurve", "cutpoly", "tracepoly",
        "borehole", "soillayer", "soillayerheight", "insertsoillayer",
        "snap", "snaplinear", "insert", "insertpoint", "insertwaterpoint",
        "insertsubcurve", "addpoint", "addsubcurve", "addwaterpoint", "add",
        "deletepoint", "movepoint", "movepointmagnetic", "move", "movedisconnected",
        "intersectsegments", "invertdirection", "extendtosymmetryaxis",
        "symmetricclose", "copylayers", "duplicate",
    ],
    "Structures": [
        "plate", "platemat", "geogrid", "geogridmat",
        "embeddedbeamrow", "embeddedbeammat", "embeddedpilerow", "embeddedpilemat",
        "fixedendanchor", "n2nanchor", "anchormat",
        "posinterface", "neginterface", "connection",
        "linedispl", "lineload", "pointdispl", "pointload",
        "reinforcement", "rockboltsperpendicular",
        "drain", "well", "tunnel", "generatetunnel", "generatethicklining",
    ],
    "Materials": [
        "soilmat", "materialcommand", "setmaterial", "clearmaterial",
        "setdefaultmaterial", "materialfactorlabel", "loadfactorlabel",
        "adddesignapproachmateriallink", "designapproach",
    ],
    "Mesh": [
        "mesh", "meshd", "gotomesh", "viewmesh",
        "coarsen", "refine", "regenerate", "selectmeshpoints",
        "mergeequivalents",
    ],
    "Phases & Calculation": [
        "phase", "insertphase", "setcurrentphase", "gotostages",
        "activate", "deactivate",
        "calculate", "checkcalculationconditions", "predict", "preview",
        "removeintermediatesteps",
        "fieldstress", "initializerectangular",
        "displmultiplier", "loadmultiplier", "multiply",
        "contraction", "addedmass",
    ],
    "Water": [
        "waterlevel", "setwaterlevel", "setglobalwaterlevel",
        "setwaterdry", "setwaterinterpolate",
        "gotowater", "gwfbc",
        "headfunction", "dischargefunction",
        "getsoillayerlevel", "setsoillayerlevel",
        "getsoillayerporepressure", "setsoillayerporepressure",
        "createreachedwl", "createreachedwlandcontinue",
        "heatfluxfunction", "heattotalfluxfunction",
        "temperaturefunction", "transferfunction", "tfbc",
    ],
    "Navigation & Modes": [
        "gotoflow", "gotosoil", "gotostructures",
        "view", "close", "save", "clear",
    ],
    "Properties & Settings": [
        "set", "setproperties", "setcolour",
        "settoggle", "gettoggle", "delruntimetoggle",
        "setphysicalcpucount", "setundostacksize",
        "allocmem", "reportmem",
    ],
    "Import / Export": [
        "export", "import", "importcrosssection", "importfielddata",
        "generatefromfielddata",
    ],
    "Information & Inspection": [
        "info", "echo", "echotunnelvalidation", "help",
        "commands", "count", "filter", "findcutobject",
        "dump", "dumpboreholes", "dumpcutobjects", "dumpfixedendanchors",
        "dumpgeogrids", "dumpgroups", "dumplinedispls", "dumplineloads",
        "dumplines", "dumpmaterials", "dumpmeshes", "dumpn2nanchors",
        "dumpnegativeinterfaces", "dumpphases", "dumppiles", "dumpplates",
        "dumppointdispls", "dumppointloads", "dumppoints", "dumppolygons",
        "dumppositiveinterfaces", "dumpsoillayers",
        "tabulate", "getresults", "getcurveresults", "getnormal",
    ],
    "Results (Output Server)": [
        "getresults", "getsingleresult", "getcurveresults", "getcurveresultspath",
        "export", "generate",
        "structuralforcesplot", "structureplot", "linecrosssectionplot",
        "show", "hide", "slice",
        "centerline", "centerlineconfig",
        "addcurvepoint", "clearcurvepoints",
        "dump", "dumpdisplacements", "dumpfixities", "dumpfrostlines",
        "dumpphreaticlevels", "dumpwaterloads",
        "index", "info", "update",
    ],
    "Groups & Arrays": [
        "group", "groupfiltered", "ungroup",
        "arrayp", "arrayr",
    ],
    "Undo/Redo & Control": [
        "undo", "redo", "reset", "resetlocal",
        "rename", "delete", "kill",
        "raise", "raiseasync", "raisethreaded",
        "testasync", "sleep",
        "retrievesuggestedparameters",
        "generateintersectionpoints",
        "writephasestomesh",
    ],
}


def strip_boilerplate(text: str) -> str:
    """Remove repeated helper function definitions."""
    lines = text.split("\n")
    result = []
    skip_until_blank = False
    in_helper_func = False
    brace_depth = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this line starts a known helper function
        is_helper = any(h in line for h in HELPER_FUNCS)
        
        if is_helper and "```python" not in line:
            # Skip the entire function (until we hit the next ``` or ## heading)
            in_helper_func = True
            # Find the code block end
            while i < len(lines) and lines[i] != "```":
                i += 1
            # Don't skip the ``` closing
            continue
        
        # Skip standard intro paragraph
        if "The remote scripting server in PLAXIS 2D Input" in line:
            i += 1
            continue
        if line.startswith("# Python wrapper commands ["):
            i += 1
            continue
            
        result.append(line)
        i += 1
    
    return "\n".join(result)


def clean_section(text: str) -> str:
    """Clean a command section: remove boilerplate, keep only the actual command docs."""
    lines = text.split("\n")
    result = []
    in_code_block = False
    skip_func = False
    
    for line in lines:
        if line.strip().startswith("```python"):
            in_code_block = True
            result.append(line)
            continue
        if line.strip() == "```" and in_code_block:
            in_code_block = False
            if not skip_func:
                result.append(line)
            skip_func = False
            continue
        
        if in_code_block:
            # Check if this code block is just a helper function def
            if any(h in line for h in HELPER_FUNCS):
                skip_func = True
            if not skip_func:
                result.append(line)
        else:
            # Skip boilerplate text
            if "The remote scripting server in PLAXIS 2D Input" in line:
                continue
            if line.startswith("# Python wrapper commands ["):
                continue
            result.append(line)
    
    # Remove empty code blocks
    cleaned = "\n".join(result)
    cleaned = re.sub(r'```python\s*```', '', cleaned)
    # Remove excessive blank lines
    cleaned = re.sub(r'\n{4,}', '\n\n\n', cleaned)
    return cleaned.strip()


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        full_text = f.read()
    
    # Split into sections by ## headers
    sections = re.split(r'^(## (?:INPUT|OUTPUT): .+)$', full_text, flags=re.MULTILINE)
    
    commands = {}  # (type, name) -> content
    current_header = None
    
    for part in sections:
        if part.startswith("## INPUT: ") or part.startswith("## OUTPUT: "):
            current_header = part.strip()
        elif current_header:
            cmd_type = "INPUT" if "INPUT:" in current_header else "OUTPUT"
            cmd_name = current_header.split(": ", 1)[1]
            cleaned = clean_section(part)
            if cleaned:
                commands[(cmd_type, cmd_name)] = cleaned
            current_header = None
    
    print(f"Parsed {len(commands)} command sections", file=sys.stderr)
    
    # Build the reference document
    out = []
    out.append("# PLAXIS 2D Python Scripting - Agent Quick Reference")
    out.append("")
    out.append("Complete reference for 243 Plaxis 2D scripting commands.")
    out.append("For full examples with helper functions, see `plaxis_2d_commands.md`.")
    out.append("")
    out.append("## Connection")
    out.append("```python")
    out.append("from plxscripting.easy import new_server")
    out.append("s_i, g_i = new_server('localhost', 10000, password='pw')  # Input")
    out.append("s_o, g_o = new_server('localhost', 10001, password='pw')  # Output")
    out.append("```")
    out.append("")
    out.append("## Common Helper Functions")
    out.append("Many notebooks use these standard helper functions for setup:")
    out.append("- `create_geometry(s_i, g_i)` — Creates soil polygon, plate, line load with dynamic multiplier")
    out.append("- `simple_test_case(s_i, g_i)` — Creates geometry, meshes, returns (s_o, g_o)")
    out.append("- `dynamic_test_case(s_i, g_i)` — Creates geometry with dynamic phase")
    out.append("- `embeddedbeam_test_case(s_i, g_i)` — Creates geometry with embedded beam")
    out.append("- `suction_test_case(s_i, g_i)` — Creates geometry with GW flow BCs")
    out.append("")
    out.append("## Key Object References")
    out.append("| Object | Description |")
    out.append("|--------|-------------|")
    out.append("| `g_i` | Input global environment |")
    out.append("| `s_i` | Input application server |")
    out.append("| `g_o` | Output global environment |")
    out.append("| `s_o` | Output application server |")
    out.append("| `g_i.Phases` | List of all phases |")
    out.append("| `g_i.InitialPhase` | The initial phase |")
    out.append("| `g_i.Soils` | List of all soil layers |")
    out.append("| `g_i.Plates` | List of all plates |")
    out.append("| `g_i.Lines` | List of all lines |")
    out.append("| `g_i.Points` | List of all points |")
    out.append("| `g_i.EmbeddedBeamRows` | List of all embedded beams |")
    out.append("| `g_i.LineLoads` | List of all line loads |")
    out.append("| `g_i.PointLoads` | List of all point loads |")
    out.append("| `g_i.Materials` | List of all materials |")
    out.append("| `g_o.ResultTypes` | Available result types |")
    out.append("| `g_o.Phases` | Output phases for results |")
    out.append("| `g_o.Plots` | Output plots list |")
    out.append("| `g_o.CenterLines` | Output centerlines |")
    out.append("")
    out.append("## All Result Types (g_o.ResultTypes)")
    out.append("| Category | Type | Description |")
    out.append("|----------|------|-------------|")
    out.append("| Soil | `.Soil.Ux` | Horizontal displacement |")
    out.append("| Soil | `.Soil.Uy` | Vertical displacement |")
    out.append("| Soil | `.Soil.Utot` | Total displacement |")
    out.append("| Soil | `.Soil.Suction` | Soil suction |")
    out.append("| Soil | `.Soil.SigmaXX` | Stress XX |")
    out.append("| Soil | `.Soil.SigmaYY` | Stress YY |")
    out.append("| Soil | `.Soil.SigmaXY` | Stress XY |")
    out.append("| EmbeddedBeamRow | `.EmbeddedBeamRow.Utot` | Beam total displacement |")
    out.append("| CenterLine | `.CenterLine.M2D` | Bending moment |")
    out.append("")
    
    # --- COMMAND INDEX ---
    out.append("---")
    out.append("")
    out.append("## Command Index")
    out.append("")
    
    input_cmds = sorted([name for (t, name) in commands if t == "INPUT"])
    output_cmds = sorted([name for (t, name) in commands if t == "OUTPUT"])
    
    out.append(f"### Input Commands ({len(input_cmds)})")
    out.append(", ".join(f"`{c}`" for c in input_cmds))
    out.append("")
    out.append(f"### Output Commands ({len(output_cmds)})")
    out.append(", ".join(f"`{c}`" for c in output_cmds))
    out.append("")
    
    # --- ALL COMMANDS ---
    out.append("---")
    out.append("")
    out.append("# INPUT COMMANDS")
    out.append("")
    
    for cmd_name in input_cmds:
        content = commands.get(("INPUT", cmd_name), "")
        if content:
            out.append(f"## g_i.{cmd_name}")
            out.append("")
            out.append(content)
            out.append("")
            out.append("---")
            out.append("")
    
    out.append("# OUTPUT COMMANDS")
    out.append("")
    
    for cmd_name in output_cmds:
        content = commands.get(("OUTPUT", cmd_name), "")
        if content:
            out.append(f"## g_o.{cmd_name}")
            out.append("")
            out.append(content)
            out.append("")
            out.append("---")
            out.append("")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    
    line_count = len(out)
    print(f"Written {line_count} lines to {OUTPUT_FILE}", file=sys.stderr)


if __name__ == "__main__":
    main()
