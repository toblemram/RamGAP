# PLAXIS 2D Python Scripting - Complete Command Reference

This document contains ALL Plaxis 2D Python scripting commands
extracted from the official Jupyter reference notebooks.

## Connection Setup

```python
from plxscripting.easy import new_server
# Input server (for building/modifying models)
s_i, g_i = new_server('localhost', 10000, password='your_password')
# Output server (for extracting results)
s_o, g_o = new_server('localhost', 10001, password='your_password')
```

---

# PART 1: INPUT COMMANDS

Input commands are used with the Input server (g_i, s_i) to
create geometry, assign materials, configure phases, and set up models.

## INPUT: activate

# Python wrapper commands [ACTIVATE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## activate
Activates features.

```python
s_i.new()
```

```python
# Alternative 1
# Activates a feature in one or more phases

# Example 1
# Creates a soil polygon, adds a plate feature, and activates the plate in two phases
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))
g_i.plate((1, 1), (2, 2))

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
phase2_s = g_i.phase(phase0_s)
plate_s = g_i.Plates[-1]

print(plate_s.activate(phase0_s, phase1_s))

# Example 2
line_s = g_i.Lines[-1]

print(line_s.activate(phase0_s, phase2_s))
```

```python
s_i.new()
```

```python
# Alternative 2
# Activates one or more activatable objects in one or more phases.

# Example 1
# Creates a soil polygon, adds plate features, and activates the plates in two phases
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))
g_i.plate((0, 0), (0, 2), (2, 2)) 

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
plates_s = g_i.Plates

print(g_i.activate((plates_s[-1], plates_s[-2]), (phase0_s, phase1_s)))

# Example 2
phase2_s = g_i.phase(phase1_s)

print(g_i.activate((plates_s[-1], plates_s[-2]), phase1_s, phase2_s))
```

---

## INPUT: add

# Python wrapper commands [ADD]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## add
Adds a segment to a polycurve or a row to an advanced table.

```python
s_i.new()
```

```python
# Alternative 1
# Adds a line section with a length of 1 to a polycurve.
polycurve_g = g_i.polycurve(4, 5)

segment_g = polycurve_g.add() 
print(segment_g)
```

```python
s_i.new()
```

```python
# Alternative 2
# Adds one or more sections with specified properties to a polycurve.

# Creates multiple objects, the first one is the Polycurve object
polycurve_g = g_i.polycurve((4, 5), "line", 0, 2, "arc", 45, 90, 3)[0]

segments_g = polycurve_g.add("arc", 0, 45, 1, "line", 90, 2)
print(segments_g)
```

```python
# Alternative 3
# Adds an empty row to an advanced table.

# Example 1
loadmultiplier_i = g_i.loadmultiplier()

row_i = loadmultiplier_i.Table.add()
print(row_i)
# Example 2
displacementmultiplier_i = g_i.displmultiplier()

row_i = displacementmultiplier_i.Table.add()
print(row_i)
```

```python
# Alternative 4
# Adds a row with specified values to an advanced table.

# Example 1
loadmultiplier_i = g_i.loadmultiplier()

row_i = loadmultiplier_i.Table.add(5, 2)
print(row_i)

# Example 2
displacementmultiplier_i = g_i.displmultiplier()

row_i = displacementmultiplier_i.Table.add(5, 2)
print(row_i)
```

```python
print(type(g_i))
print(type(s_i))
```

```python
def list_public_methods(obj):
    return sorted([
        m for m in dir(obj)
        if not m.startswith("_")
    ])

methods = list_public_methods(g_i)

for m in methods[:50]:
    print(m)

print(f"\nTotalt antall metoder: {len(methods)}")
```

```python
import inspect

func = g_i.adam

print("SIGNATURE:")
print(inspect.signature(func))

print("\nDOCSTRING:")
print(inspect.getdoc(func))
```

```python
import json
import re

with open("contents_2d.ipynb", encoding="utf-8") as f:
    nb = json.load(f)

pattern = re.compile(r"g_i\.(\w+)\((.*?)\)")

calls = {}

for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    source = "".join(cell["source"])
    for match in pattern.finditer(source):
        name = match.group(1)
        args = match.group(2)
        calls.setdefault(name, set()).add(args)

for name, args in calls.items():
    print(name)
    for a in args:
        print("  ", a)
```

```python
import os
os.getcwd()
```

```python
os.listdir()
```

```python
import json

path = r"c:\users\public\documents\bentley\geotechnical\plaxis 2d connect edition v20 update 3\jupyter reference notebooks\input_notebooks\2d-python-inputcommands-addpoint.ipynb"

with open(path, encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb["cells"]:
    print(cell["cell_type"])
    print("".join(cell["source"]))
    print("-" * 40)
```

```python
import json

cells = nb["cells"]

markdown_blocks = []
code_blocks = []

for cell in cells:
    if cell["cell_type"] == "markdown":
        markdown_blocks.append("".join(cell["source"]))
    elif cell["cell_type"] == "code":
        code_blocks.append("".join(cell["source"]))
```

```python
import os
import json
import re

# --- KONFIGURASJON ---
INPUT_DIR = r"c:\users\public\documents\bentley\geotechnical\plaxis 2d connect edition v20 update 3\jupyter reference notebooks\input_notebooks"
OUTPUT_DIR = r"C:\Users\TBLM\OneDrive - Ramboll\Documents\pl_cards"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Hjelpefunksjon: hent kommando-navn fra filnavn
def command_name_from_filename(filename):
    # Eksempel:
    # 2d-python-inputcommands-addpoint.ipynb -> addpoint
    name = filename.lower()
    name = re.sub(r"\.ipynb$", "", name)
    name = re.sub(r"^2d-python-inputcommands-", "", name)
    return name

# --- HOVEDLOOP ---
for filename in os.listdir(INPUT_DIR):
    if not filename.endswith(".ipynb"):
        continue

    input_path = os.path.join(INPUT_DIR, filename)
    command_name = command_name_from_filename(filename)
    output_path = os.path.join(OUTPUT_DIR, f"{command_name}.txt")

    with open(input_path, encoding="utf-8") as f:
        nb = json.load(f)

    lines = []

    for cell in nb.get("cells", []):
        cell_type = cell.get("cell_type")
        source = "".join(cell.get("source", []))

        if not source.strip():
            continue

        if cell_type == "markdown":
            lines.append(source.strip())

        elif cell_type == "code":
            lines.append("```python")
            lines.append(source.rstrip())
            lines.append("```")

    # Skriv kortet
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(lines))

    print(f"✔ Laget kort: {command_name}.txt")

print("\n🎉 Ferdig! Alle kort generert.")
```

---

## INPUT: adddesignapproachmateriallink

# Python wrapper commands [ADDDESIGNAPPROACHMATERIALLINK]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## adddesignapproachmateriallink 
 Adds design approach material factor to a material parameter.

```python
s_i.new()
```

```python
# Alternative 1
# Adds design approach material factor to a material parameter.

# Creates a material, material factor label, design approach
material_i = g_i.soilmat("MaterialName", "Sand", "SoilModel", 1, 
                         "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
material_factor_label_i = g_i.materialfactorlabel()
design_approach_i = g_i.designapproach()

g_i.adddesignapproachmateriallink(design_approach_i, material_i.gammaSat, material_factor_label_i)
```

```python
# Alternative 2
# Adds design approach material factor to a material parameter.

g_i.adddesignapproachmateriallink(design_approach_i, material_i.gammaSat, 3, material_factor_label_i)
```

---

## INPUT: addedmass

# Python wrapper commands [ADDEDMASS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## addedmass
Adds Westergaard AddedMass feature features to lines.

```python
s_i.new()
```

```python
# Alternative 1
# Adds Westergaard AddedMass features to one or more existing lines in the geometry.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((2, 2), (3, 3))[-1]
addedmass_g = g_i.addedmass(line_g)
print(addedmass_g)

# Example 2
# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((0, 2), (2, 2))[-1]
line2_g = g_i.line((2, 2), (2, 0))[-1]
addedmasses_g = g_i.addedmass(line1_g, line2_g)
print(addedmasses_g)
```

```python
s_i.new()
```

```python
# Alternative 2
# Creates a line between two points (which may either exist, or will be created) and add a Westergaard AddedMass feature to it.

# Example 1
# Creates multiple objects, the last one is the Westergaard AddedMass object ([-1])
point_g = g_i.point(0, 0)
addedmass_g = g_i.addedmass(point_g, (5, 6))[-1]
print(addedmass_g)

# Example 2
points_g = g_i.point((1, 1), (1, 4))
line_g, addedmass_g = g_i.addedmass(points_g[-2], points_g[-1])
print(addedmass_g)

# Example 3
# Creates multiple objects, the last one is the Westergaard AddedMass object ([-1])
addedmass_g = g_i.addedmass((5, 5), (5, 2))[-1]
print(addedmass_g)
```

```python
s_i.new()
```

```python
# Alternative 3
# Creates lines between three or more points (which may either exist, or will be created) and add Westergaard AddedMass features to them.

points_g = g_i.point((1, 1), (4, 4))
res = g_i.addedmass(points_g[-2], (2, 3), points_g[-1])
addedmasses_g = [item for item in res if item._plx_type == 'AddedMass']
print(addedmasses_g)
```

```python
s_i.new()
```

```python
# Alternative 4
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect
# to the xy-plane and a length or a vector describing the direction and a length and add Westergaard AddedMass features to them.

# Example 1
# Creates multiple objects, the last one is the Westergaard AddedMass object ([-1])
addedmass_g = g_i.addedmass((1, 2), "relative", (3, 4))[-1]
print(addedmass_g)

# Example 2
point_g = (1, 2)
res = g_i.addedmass(point_g, "relative", (3, 4), (-5, -9), "angles", 30, 16)
addedmasses_g = [item for item in res if item._plx_type == 'AddedMass']
print(addedmasses_g)

# Example 3
res = g_i.addedmass((1, 2), "angles", 45, 10, "absolute", (4, 5))
addedmasses_g = [item for item in res if item._plx_type == 'AddedMass']
print(addedmasses_g)
```

```python
s_i.new()
```

```python
# Alternative 5
# Adds Westergaard AddedMass features to one or more existing lines in the geometry and directly set their properties.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((2, 2), (3, 3))[-1]
addedmass_g = g_i.addedmass(line_g, "PositiveWBL", 1.2)
print(addedmass_g)

# Example 2
line1_g = g_i.line((2, 4), (3, 4))[-1]
line2_g = g_i.line((0, 2), (1, 2))[-1]
addedmassess_g = g_i.addedmass(line1_g, line2_g, "NegativeWBL", 1.2)
print(addedmasses_g)
```

```python
s_i.new()
```

```python
# Alternative 6
# Creates a line between two points (which may either exist, or will be created), add a Westergaard AddedMass feature to it and directly set its properties.

# Creates multiple objects, the last one is the Westergaard AddedMass object ([-1])
point_g = g_i.point(1, 1)
addedmass_g = g_i.addedmass(point_g, (5, 6), "PositiveWBL", 1.2)[-1]
print(addedmass_g)
```

```python
s_i.new()
```

```python
# Alternative 7
# Creates lines between three or more points (which may either exist, or will be created), add Westergaard AddedMass features to them and directly set their properties.

point1_g, point2_g = g_i.point((1, 1), (8, 9))
res = g_i.addedmass(point1_g, (5.1, 6.4), point2_g, "NegativeWBL", 1.2)
addedmasses_g = [item for item in res if item._plx_type == 'AddedMass']
print(addedmasses_g)
```

```python
# Alternative 8
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect 
# to the xy-plane and a length or a vector describing the direction and a length, add Westergaard AddedMass features to them and directly set their properties.

# Creates multiple objects, the last one is the Westergaard AddedMass object ([-1])
addedmass_g = g_i.addedmass((1, 2), "relative", (3, 4), "PositiveWBL", 1.2)[-1]
print(addedmass_g)
```

---

## INPUT: addpoint

# Python wrapper commands [ADDPOINT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## addpoint
Adds a new point to a polygon or water level.

```python
s_i.new()
```

```python
# Alternative 1
# Adds a new point to an existing polygon.

# Creates multiple objects, the first one is the Polygon object
polygon_g = g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))[0]
polygon_g.addpoint(0, -2)
```

```python
# Alternative 2
# Adds two or more new points to an existing polygon.

# Creates multiple objects, the first one is the Polygon object
polygon_g = g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))[0]
polygon_g.addpoint((0, -2), (2, 7))
```

```python
s_i.new()
```

```python
# Alternative 3
# Adds a new water point to an existing water level without specifying the pinc.

g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))

g_i.gotoflow()
waterlevel_s = g_i.waterlevel((1, 4), (2, 4))

waterlevel_s.addpoint(4, 3)
```

```python
s_i.new()
```

```python
# Alternative 4
# Adds two or more new water points to an existing water level without specifying the pinc.

g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))

g_i.gotoflow()
waterlevel_s = g_i.waterlevel((1, 4), (2, 4))

waterlevel_s.addpoint((3, 3), (4, 3.5))
```

---

## INPUT: addsubcurve

# Python wrapper commands [ADDSUBCURVE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## addsubcurve
Adds a subcurve to a tunnel cross section.

```python
s_i.new()
```

```python
# Alternative 1
# Adds a sub section to a tunnel cross section.

tunnel_g = g_i.tunnel(6, 2)
# Creates multiple objects, SubsectionPolycurve and Segment objects
subsectionpolycurve_g, segment_g = tunnel_g.CrossSection.addsubcurve()
print(subsectionpolycurve_g, segment_g)
```

```python
# Alternative 2
# Adds one or more sub sections with specified properties to a tunnel cross section.

# Example 1
tunnel_g = g_i.tunnel(0, 0)
# Creates multiple objects, SubsectionPolycurve and Segment objects
subsectionpolycurve_g, segment_g = tunnel_g.CrossSection.addsubcurve("Line", 2, 3, 180, 1)
print(subsectionpolycurve_g, segment_g)

# Example 2
tunnel_g = g_i.tunnel(1, 1)
# Creates multiple objects, SubsectionPolycurve and Segment objects
subsectionpolycurve_g, segment_g = tunnel_g.CrossSection.addsubcurve("Arc", 2, 3, 0, 90, 1)
print(subsectionpolycurve_g, segment_g)
```

---

## INPUT: addwaterpoint

# Python wrapper commands [ADDWATERPOINT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## addwaterpoint
Adds a point to a water level.

```python
s_i.new()
```

```python
# Alternative 1
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))

g_i.gotoflow()
waterlevel_s = g_i.waterlevel((1, 2), (2, 2))

waterlevel_s.addwaterpoint((3, 3), -5)
```

---

## INPUT: allocmem

# Python wrapper commands [ALLOCMEM]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## allocmem
Tests if it is possible to allocate a specific amount of additional memory.

```python
s_i.new()
```

```python
# Alternative 1
try:
    g_i.allocmem(64)
except:
    print("Allocated 64 MB")
```

---

## INPUT: anchormat

# Python wrapper commands [ANCHORMAT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## anchormat
Creates an anchor material set.

```python
s_i.new()
```

```python
# Alternative 1
g_i.anchormat()
```

---

## INPUT: apply

# Python wrapper commands [APPLY]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## apply
Applies a command to multiple objects at once.

```python
s_i.new()
```

```python
# Alternative 1
# Applies a command to multiple objects at once. Every time a command is applied to an object an undo-able action is created.

point1_g, point2_g, point3_g = g_i.point((6, 4), (9, 8), (4, 1))
points_g = g_i.Points

print(g_i.apply(points_g, "echo"))
```

```python
s_i.new()
```

```python
# Alternative 2
# Applies a command to multiple objects at once. Every time a command is applied to an object an undo-able action is created.

# Example 1
point1_g, point2_g, point3_g = g_i.point((6, 4), (9, 8), (4, 1))
points_g = g_i.Points

print(g_i.apply(points_g, "setproperties", "x", 3))

# Example 2
# Clears the current geometry, creates a polygon and defines 5 phases
g_i.clear()
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))

g_i.gotostages()
phases_s = [g_i.phase(g_i.Phases[i]) for i in range(5)]
phases_s = g_i.Phases

print(g_i.apply(phases_s, "setproperties", "MaxCores", 4))

# Example 3
# Changes the mode, creates two n2n anchors and defines their properties in Phase_1
g_i.gotostructures()
# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((0, 2), (-5, 2))[-1] 
line2_g = g_i.line((1, 2), "relative", (3, 4))[-1]
g_i.n2nanchor(line1_g, line2_g)

g_i.gotostages()
phases_s = [g_i.phase(g_i.Phases[i]) for i in range(5)]
nodetonodeanchors_s = g_i.NodeToNodeAnchors

print(g_i.apply(nodetonodeanchors_s, "sps", "AdjustPrestress", phases_s[1], True))
```

---

## INPUT: arrayp

# Python wrapper commands [ARRAYP]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## arrayp
Creates a polar array from one or more objects.

```python
s_i.new()
```

```python
# Alternative 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((0, 2), (2, 2))[-1] 
res = g_i.arrayp(line_g, (0, 0), 180, 4, True)
lines_g = [item for item in res if item._plx_type == 'Line']
print(lines_g)
```

---

## INPUT: arrayr

# Python wrapper commands [ARRAYR]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## arrayr
Creates a rectangular array from one or more objects.

```python
s_i.new()
```

```python
# Alternative 1
# Creates an array from a borehole, with a specified number of new boreholes at a specified interval.

borehole1_g = g_i.borehole(0)
boreholes_g = g_i.arrayr(borehole1_g, 4, 5)
print(boreholes_g)
```

```python
s_i.new()
```

```python
# Alternative 2
# Creates an array from a selected object, with a specified number of rows at the specified intervals.

point1_g = g_i.point(2, 3)
points_g = g_i.arrayr(point1_g, 2, (1, 5), 3, (6, 4))
print(points_g)
```

```python
s_i.new()
```

```python
# Alternative 3
# Creates an array from a selected object, with a specified number of new objects at a specific interval.

point1_g = g_i.point(2, 3)
points_g = g_i.arrayr(point1_g, 3, (1, 0))
print(points_g)
```

---

## INPUT: borehole

# Python wrapper commands [BOREHOLE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## borehole
Creates a borehole.

```python
s_i.new()
```

```python
# Alternative 1
borehole_g = g_i.borehole(0)
print(borehole_g)
```

---

## INPUT: calculate

# Python wrapper commands [CALCULATE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## calculate
Calculates all phases that are currently marked for calculation.

```python
s_i.new()
```

```python
# Alternative 1
# Calculates all phases that are currently marked for calculation.

# Creates a borehole, soillayer, assigns material to the soil, and creates line load
borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[0].Material = material
g_i.gotostructures()
g_i.lineload((3, 0), (7, 0))

# Generates the mesh, defines the phases, activates the line load
g_i.gotomesh()
g_i.mesh(0.2)

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
g_i.LineLoads[-1].Active[phase1_s] = True
g_i.calculate()
```

```python
s_i.new()
```

```python
# Alternative 2
# Calculates one or more explicitly specified phases, regardless of whether they are currently marked for calculation.

# Creates a borehole, soillayer, assigns material to the soil, and creates line loads
borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[0].Material = material
g_i.gotostructures()
g_i.lineload((3, 0), (4, 0))
g_i.lineload((5, 0), (7, 0))

# Generates the mesh, defines the phases, activates the line loads in different phases 
g_i.gotomesh()
g_i.mesh(0.2)

g_i.gotostages()
phase0_s = g_i.InitialPhase
phases_s = [g_i.phase(phase0_s) for i in range(6)]

lineload1_s = g_i.LineLoads[-2]
lineload2_s = g_i.LineLoads[-1]

lineload1_s.Active[phases_s[0]] = True
lineload2_s.Active[phases_s[5]] = True
print(g_i.calculate(g_i.Phases[0]))

print(g_i.calculate(phases_s[0], phases_s[5]))

# Obtain Identification value assigned for all phases in a list and display them
phases_id = g_i.Phases.Identification.value
print(f'Phases Identification property: {phases_id}')
```

```python
s_i.new()
```

```python
# Alternative 3
# Calculates all phases that are currently marked for calculation with the possibility to also calculate the phases that are currently not marked for calculation.

# Example 1
# Creates a borehole, soillayer, assigns material to the soil, and creates a load feature
borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[0].Material = material

g_i.gotostructures()
g_i.lineload((3, 0), (7, 0))

# Generates the mesh and defines the phases
g_i.gotomesh()
g_i.mesh(0.2)

g_i.gotostages()
phase0_s = g_i.InitialPhase
phases_s = [g_i.phase(phase0_s) for i in range(5)]
for phase in phases_s[2:4]:
    phase.ShouldCalculate = False

g_i.LineLoads[-1].Active[phases_s[0]] = True
print(g_i.calculate(True))

# Example 2
# Changes the mode, and activates the line load in one phase

g_i.gotostages()
g_i.LineLoads[-1].Active[phases_s[0]] = True

for phase in phases_s[0:1]:
    phase.ShouldCalculate = True
print(g_i.calculate(False))
```

---

## INPUT: checkcalculationconditions

# Python wrapper commands [CHECKCALCULATIONCONDITIONS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## checkcalculationconditions
Performs the pre-calculation checks on conditions and settings of the defined phases.

```python
s_i.new()
```

```python
# Alternative 1
# Performs the pre-calculation checks on conditions and settings of all phases and reports all warnings and errors.

# Creates a borehole, soillayer, assigns material to the soil and creates lineload, anchor and plate features
borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[0].Material = material
g_i.gotostructures()
g_i.lineload((3, 0), (5, 0))
g_i.n2nanchor((5, 0), (6, 0))
g_i.plate((7, 0), (8, 0))

# Generates the mesh, defines the phases, activates the line load
g_i.gotomesh()
g_i.mesh(0.2)

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
g_i.LineLoads[-1].Active[phase1_s] = True

print(g_i.checkcalculationconditions())
```

```python
s_i.new()
```

```python
# Alternative 2
# Performs the pre-calculation checks on conditions and settings of specific phases.

# Creates a borehole, soillayer, assigns material to the soil and creates lineload, anchor and plate features
borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[0].Material = material
g_i.gotostructures()
g_i.lineload((3, 0), (5, 0))
g_i.n2nanchor((5, 0), (6, 0))
g_i.plate((7, 0), (8, 0))

# Generates the mesh, defines the phases, activates the line load
g_i.gotomesh()
g_i.mesh(0.2)

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
g_i.LineLoads[-1].Active[phase1_s] = True

print(g_i.checkcalculationconditions(phase1_s))
```

```python
s_i.new()
```

```python
# Alternative 3
# Performs the pre-calculation checks on conditions and settings of the phases but report only the errors.

# Creates a borehole, soillayer, assigns material to the soil and creates lineload, anchor and plate features
borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[0].Material = material
g_i.gotostructures()
g_i.lineload((3, 0), (5, 0))
g_i.n2nanchor((5, 0), (6, 0))
g_i.plate((7, 0), (8, 0))

# Generates the mesh, defines the phases, activates the line load
g_i.gotomesh()
g_i.mesh(0.2)

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
g_i.LineLoads[-1].Active[phase1_s] = True

print(g_i.checkcalculationconditions(phase1_s, "errors"))
```

```python
s_i.new()
```

```python
# Alternative 4
# Performs the pre-calculation checks on conditions and settings of all phases and reports the selected level of check: errors, warnings, hints and tips.

# Creates a borehole, soillayer, assigns material to the soil and creates lineload, anchor and plate features
borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[0].Material = material
g_i.gotostructures()
g_i.lineload((3, 0), (5, 0))
g_i.n2nanchor((5, 0), (6, 0))
g_i.plate((7, 0), (8, 0))

# Generates the mesh, defines the phases, activates the line load
g_i.gotomesh()
g_i.mesh(0.2)

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
g_i.LineLoads[-1].Active[phase1_s] = True

print(g_i.checkcalculationconditions("errors"))
```

```python
s_i.new()
```

```python
# Alternative 5
# Performs the pre-calculation checks on conditions and settings of a phase listable and reports all: errors, warnings, hints and tips.

# Creates a borehole, soillayer, assigns material to the soil and creates lineload, anchor and plate features
borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[0].Material = material

g_i.gotostructures()
g_i.lineload((3, 0), (7, 0))
g_i.n2nanchor((5, 0), (6, 0))
g_i.plate((7, 0), (8, 0))

# Generates the mesh and defines the phases
g_i.gotomesh()
g_i.mesh(0.2)

g_i.gotostages()
phase0_s = g_i.InitialPhase
phases_s = [g_i.phase(phase0_s) for i in range(4)]
group_s = g_i.group(phase0_s, phases_s[0], phases_s[1])

print(g_i.checkcalculationconditions(group_s))
```

```python
s_i.new()
```

```python
# Alternative 6
# Performs the pre-calculation checks on conditions and settings of a phase listable and reports the selected level of check: errors, warnings, hints and tips.

# Creates a borehole, soillayer, assigns material to the soil and creates lineload, anchor and plate features
borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[0].Material = material

g_i.gotostructures()
g_i.lineload((3, 0), (7, 0))
g_i.n2nanchor((5, 0), (6, 0))
g_i.plate((7, 0), (8, 0))

# Generates the mesh and defines the phases
g_i.gotomesh()
g_i.mesh(0.2)

g_i.gotostages()
phase0_s = g_i.InitialPhase
phases_s = [g_i.phase(phase0_s) for i in range(4)]
group_s = g_i.group(phase0_s, phases_s[2])

print(g_i.checkcalculationconditions(group_s, "errors"))
```

---

## INPUT: checkgeometry

# Python wrapper commands [CHECKGEOMETRY]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## checkgeometry
Checks geometry consistency. Checks if objects overlap or are adjacent and then returns them.

```python
s_i.new()
```

```python
# Alternative 1
# Creates multiple objects, the first one is the Polygon object ([0])
polygon_g = g_i.polygon((0, 0), (0, 2), (2, 2), (2, 0))[0]
g_i.point((0.01, 0.01), (0.01, 2.01))
print(g_i.checkgeometry())
```

```python
s_i.new()
```

```python
# Alternative 2
# Creates multiple objects, the first one is the Polygon object ([0])
polygon_g = g_i.polygon((0, 0), (0, 2), (2, 2), (2, 0))[0]
g_i.point((1, 2), (2, 1))
print(g_i.checkgeometry(3))
```

---

## INPUT: clear

# Python wrapper commands [CLEAR]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## clear
Deletes all objects.

```python
s_i.new()
```

```python
# Alternative 1
# Creates a borehole, points, line and clears the geometrical entities
g_i.borehole(0)
g_i.point(3, 4)
g_i.line((5, 6), (8, 9))
g_i.clear()
```

---

## INPUT: clearmaterial

# Python wrapper commands [CLEARMATERIAL]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## clearmaterial
Clears the assignment of the Material property of any Soil or Structure object in any mode.

```python
s_i.new()
```

```python
# Alternative 1
# Clears the assignment of the Material property of a specific Soil object in Structures mode.

# Creates a borehole, soillayer, assigns material to the soil and clears the assignement of that Soil object.
borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[0].Material = material
g_i.clearmaterial(g_i.Soils[0])
```

```python
s_i.new()
```

```python
# Alternative 2
# Clears the assignment of the Material property of a specific Structure object in Structures mode.

# Creates a borehole, soillayer, assigns material to the soil, creates a plate, creates the plate material, assigns the plate material to the plate and clears the assignement of that Structure object.
borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[0].Material = material

g_i.gotostructures()
plate_g = g_i.plate(0, 0, 3, 0)
plate_mat = g_i.platemat()
plate_mat.setproperties("MaterialName", "Footing", "Gref", 351.10420352895267, 
                        "d", 1.0954451150103321, "nu", 0.3, "EA", 1000, "EA2", 1000, "EI", 100)
g_i.Plates[0].Material = plate_mat
g_i.clearmaterial(g_i.Plates[0])
```

```python
s_i.new()
```

```python
# Alternative 3
# Clear the assignment of the Material property of a Structure object in Structures mode.

# # Creates a borehole, soillayer, assigns material to the soil, creates two plates, creates one plate material, assigns the plate material to both Structure objects and clears the assignement of both Structure objects.
borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[0].Material = material

g_i.gotostructures()
plate1_g = g_i.plate(0, 0, 3, 0)
plate2_g = g_i.plate(3, 0, 5, 0)
plate_mat = g_i.platemat()
plate_mat.setproperties("MaterialName", "Footing", "Gref", 351.10420352895267, 
                        "d", 1.0954451150103321, "nu", 0.3, "EA", 1000, "EA2", 1000, "EI", 100)
g_i.Plates[0].Material = plate_mat
g_i.Plates[1].Material = plate_mat
g_i.clearmaterial(g_i.Plates[0], g_i.Plates[1])
```

```python
s_i.new()
```

```python
# Alternative 4
# Clear the assignment of the Material property of a Soil and Structure object in two phases in Staged construction mode.

# Creates a borehole, soillayer, assigns material to the soil, creates two plates, creates one plate material and assigns the plate material to both Structure objects.
borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[0].Material = material

g_i.gotostructures()
plate1_g = g_i.plate(0, 0, 3, 0)
plate2_g = g_i.plate(3, 0, 5, 0)
plate_mat = g_i.platemat()
plate_mat.setproperties("MaterialName", "Footing", "Gref", 351.10420352895267, 
                        "d", 1.0954451150103321, "nu", 0.3, "EA", 1000, "EA2", 1000, "EI", 100)
g_i.Plates[0].Material = plate_mat
g_i.Plates[1].Material = plate_mat

# Generates the mesh, defines the phases, and clears the assignement of the Soil and one of the Structure objects in both phases in Staged construction mode.
g_i.gotomesh()
g_i.mesh(0.2)

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
g_i.clearmaterial((g_i.Soils[0], g_i.Plates[1]), (g_i.Phases[0], g_i.Phases[1]))
```

```python
s_i.new()
```

```python
# Alternative 5
# Clear the assignment of the Material property of a Soil and Structure object in multiple phases in Staged construction mode.

# Creates a borehole, a soillayer, assigns the material to the soil, creates a plate, creates a plate material and assigns the plate material to the Structure objects.
borehole_g = g_i.borehole(0)
g_i.soillayer(10)

material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[0].Material = material

g_i.gotostructures()
plate_g = g_i.plate(0, 0, 3, 0)
plate_mat = g_i.platemat()
plate_mat.setproperties("MaterialName", "Footing", "Gref", 351.10420352895267, 
                        "d", 1.0954451150103321, "nu", 0.3, "EA", 1000, "EA2", 1000, "EI", 100)
g_i.Plates[0].Material = plate_mat

# Generates the mesh, defines the phases, creates a group of both phases and clears the assignement of the group in Staged construction mode.
g_i.gotomesh()
g_i.mesh(0.2)

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
g_i.group(phase0_s, phase1_s)
g_i.clearmaterial((g_i.Soils[0], g_i.Plates[0]), (g_i.Groups[0]))
```

---

## INPUT: close

# Python wrapper commands [CLOSE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## close
Closes a polycurve.

```python
s_i.new()
```

```python
# Alternative 1
# Closes a polycurve by adding a line segment.

# Creates multiple objects, the first one is the Polycurve object
polycurve_g = g_i.polycurve((4, 5), "line", 0, 2, "arc", 45, 90, 3)[0]
segment_g = polycurve_g.close()
print(segment_g)
```

```python
# Alternative 2
# Closes a polycurve by adding a line segment.

# Creates multiple objects, the first one is the Polycurve object
polycurve_g = g_i.polycurve((0, 0), "line", 0, 2, "arc", 45, 90, 3)[0]
segment_g = polycurve_g.close("line")
print(segment_g)
```

```python
# Alternative 3
# Closes a polycurve by adding an arc segment with a specified radius.

# Creates multiple objects, the first one is the Polycurve object
polycurve_g = g_i.polycurve((8, 10), "line", 0, 2, "arc", 45, 90, 3)[0]
segment_g = polycurve_g.close("arc", 5)
print(segment_g)
```

---

## INPUT: coarsen

# Python wrapper commands [COARSEN]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## coarsen
Requests a coarser mesh for a meshable object.

```python
s_i.new()
```

```python
# Alternative 1
# Creates multiple objects, the first one is the Polygon object ([0])
polygon_g = g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))[0]
g_i.gotomesh()

g_i.coarsen(polygon_g)
```

---

## INPUT: commands

# Python wrapper commands [COMMANDS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## commands
Displays available commands and their signatures.

```python
s_i.new()
```

```python
# Alternative 1
# Displays all available global commands for the current working mode with their corresponding signature(s).

print(g_i.commands())
```

```python
# Alternative 2
# Displays the signatures of one or more global commands.

point_g = g_i.point(1, 1)
print(point_g.commands())
```

```python
# Alternative 3
# Displays all available commands for an object with their signatures.

# Example 1
print(g_i.commands("undo"))

# Example 2
print(g_i.commands("d"))
```

```python
# Alternative 4
# Identifies commands by part of their name and display the signatures of a specific command.

point_g = g_i.point(1, 1)
print(point_g.commands("m"))
```

---

## INPUT: connection

# Python wrapper commands [CONNECTION]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## connection
Creates a connection between two objects: the custom part and the reference part.

```python
s_i.new()
```

```python
# Alternative 1
# Creates a connection between two plates: the custom part and the reference part.

# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((0, 0), (2, 0))[-1] 
line2_g = g_i.line((2, 0), (2, 2))[-1]
platematerial_i = g_i.platemat()
plate1_g = g_i.plate(line1_g, "Material", platematerial_i)
plate2_g = g_i.plate(line2_g, "Material", platematerial_i)

connection_g = g_i.connection(plate1_g, plate2_g)
print(connection_g)
```

```python
s_i.new()
```

```python
# Alternative 2
# Creates a connection between two line or polycurve objects.

# Example 1
# Creates multiple objects, the first one is the Polycurve object ([0])
polycurve1_g = g_i.polycurve((0, 0), "line", 0, 2)[0]
polycurve2_g = g_i.polycurve((0, 0), "line", 90, 2)[0] 
g_i.plate(polycurve1_g, polycurve2_g)

connection_g = g_i.connection(polycurve1_g, polycurve2_g)
print(connection_g)

# Example 2
# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((2, 2), (3, 2))[-1]
line2_g = g_i.line((2, 0), (2, 2))[-1]
g_i.plate(line1_g, line2_g)

connection_g = g_i.connection(line1_g, line2_g)
print(connection_g)
```

---

## INPUT: contraction

# Python wrapper commands [CONTRACTION]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## contraction
Adds contraction features to lines.

```python
s_i.new()
```

```python
# Alternative 1
# Adds contraction features to one or more existing lines in the geometry.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((2, 2), (3, 2))[-1]
contraction_g = g_i.contraction(line_g)
print(contraction_g)

# Example 2
# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((4, 5), (6, 7))[-1]
line2_g = g_i.line((8, 9), (10, 11))[-1]
contractions_g = g_i.contraction(line1_g, line2_g)
print(contractions_g)

# Example 3
# Creates multiple objects, the first one is the Polycurve object ([0])
polycurve_g = g_i.polycurve((0, 0), "line", 0, 2, "arc", 45, 90, 1)[0]
contraction_g = g_i.contraction(polycurve_g)
print(contraction_g)
```

```python
s_i.new()
```

```python
# Alternative 2
# Creates a line between two points (which may either exist, or will be created) and add a contraction feature to it.

# Example 1
# Creates multiple objects, last two ([-2:]) are Line and LineContraction objects respectively
point_g = g_i.point(2, 3)
line_g, contraction_g = g_i.contraction(point_g, (5, 6))[-2:] 
print(contraction_g)

# Example 2
# Creates multiple objects, last two ([-2:]) are Line and LineContraction objects respectively
point1_g = g_i.point(0, 0)
point2_g = g_i.point(1, 1)
line_g, contraction_g = g_i.contraction(point1_g, point2_g)[-2:]
print(contraction_g)

# Example 3
# Creates multiple objects, last two ([-2:]) are Line and LineContraction objects respectively
line_g, contraction_g = g_i.contraction((1, 4), (6, 5))[-2:]
print(contraction_g)
```

```python
s_i.new()
```

```python
# Alternative 3
# Creates lines between three or more points (which may either exist, or will be created) and add contraction features to them.

point1_g, point2_g = g_i.point((1, 1), (8, 8))
res = g_i.contraction(point1_g, (5.1, 6.4), point2_g)
contractions_g = [item for item in res if item._plx_type == 'LineContraction']
print(contractions_g)
```

```python
s_i.new()
```

```python
# Alternative 4
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect to 
# the xy-plane and a length or a vector describing the direction and a length and add contraction features to them.

# Example 1
# Creates multiple objects, last two ([-2:]) are Line and LineContraction objects respectively
line_g, contraction_g = g_i.contraction((1, 2), "relative", (3, 4))[-2:]
print(contraction_g)

# Example 2
point1_g = g_i.point(1, 2)
res = g_i.contraction(point1_g, "relative", 3, 4, -5, -9, "angles", 30, 16)
contractions_g = [item for item in res if item._plx_type == 'LineContraction']
print(contractions_g)

# Example 3
res = g_i.contraction((1, 2), "angles", 45, 10, "absolute", (4, 5))
contractions_g = [item for item in res if item._plx_type == 'LineContraction']
print(contractions_g)
```

```python
s_i.new()
```

```python
# Alternative 5
# Adds contraction features to one or more existing lines in the geometry and directly set their properties.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((0, 0), (1, 1))[-1]
contraction_g = g_i.contraction(line_g, "C", 1.2)
print(contraction_g)

# Example 2
# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((1, 2), (2, 3))[-1]
line2_g = g_i.line((4, 5), (6, 7))[-1]
contractions_g = g_i.contraction((line1_g, line2_g), "C", 1.2)
print(contraction_g)
```

```python
# Alternative 6
# Creates a line between two points (which may either exist, or will be created), add a contraction feature to it and directly set its properties.

# Creates multiple objects, last two ([-2:]) are Line and LineContraction objects respectively
point_g = g_i.point(3, 5)
line_g, contraction_g = g_i.contraction(point_g, (5, 6), "C", 1.2)[-2:]
print(contraction_g)
```

```python
# Alternative 7
# Creates lines between three or more points (which may either exist, or will be created), add contraction features to them 
# and directly set their properties.

point1_g, point2_g = g_i.point((3, 5), (8, 9))
res = g_i.contraction(point1_g, (5.1, 6.4), point2_g, "C", 1.2)
contractions_g = [item for item in res if item._plx_type == 'LineContraction']
print(contractions_g)
```

```python
# Alternative 8
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect 
# to the xy-plane and a length or a vector describing the direction and a length, add contraction features to them and directly set their properties.

# Creates multiple objects, last two ([-2:]) are Line and LineContraction objects respectively
line_g, contraction_g = g_i.contraction((1, 2), "relative", (3, 4), "C", 1.2)[-2:]
print(contraction_g)
```

---

## INPUT: copylayers

# Python wrapper commands [COPYLAYERS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## copylayers
Copies the soil layer properties from one borehole to other boreholes.

```python
s_i.new()
```

```python
# Alternative 1
# Copies the soil layer properties from one borehole to other boreholes.

# Creates a borehole, defines soil layers 
borehole1_g = g_i.borehole(0)
g_i.soillayer(1)
g_i.soillayer(4)
soillayer1_g = g_i.Soillayers[-1]
soillayer2_g = g_i.Soillayers[-2]

borehole2_g = g_i.borehole(5)
borehole3_g = g_i.borehole(10)

g_i.soillayerheight(borehole1_g, soillayer1_g, 1)
g_i.soillayerheight(borehole1_g, soillayer2_g, 2)

g_i.copylayers(borehole1_g, (borehole2_g, borehole3_g))
```

---

## INPUT: count

# Python wrapper commands [COUNT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## count
Displays the number of objects that are present in a alistable and that, optionally, match a specified condition

```python
s_i.new()
```

```python
# Alternative 1
# Displays the number of objects of a specified type that are listed that are present.

g_i.point((1, 1), (2, 2), (3, 3))
points_g = g_i.Points
g_i.count(points_g)
```

```python
s_i.new()
```

```python
# Alternative 2
# Displays the number of objects of a specified type that are present and which fulfill a certain condition.

# Example 1
g_i.line((1, 1), (1, 2), (4, 6), (8, 7))
points_g = g_i.Points
print(g_i.count(points_g, "x>1"))

# Example 2
lines_g = g_i.Lines
print(g_i.count(lines_g, "Length>1"))
```

---

## INPUT: createreachedwl

# Python wrapper commands [CREATEREACHEDWL]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## createreachedwl
Creates a new water level at the position reached at the end of the previous phase. The location of the water level will be constant in the current phase.

```python
s_i.new()
```

```python
# Alternative 1
# Creates a borehole, soil layer
borehole_g = g_i.borehole(0)
g_i.soillayer(10)

# Changes the mode, adds a waterlevel and assigns a head function
g_i.gotoflow()
refwaterlevel_s = g_i.waterlevel((0, 4), (10, 4))
flowfunction_s = g_i.headfunction()
flowfunction_s.Signal = flowfunction_s.Signal.linear
flowfunction_s.Time = 5
flowfunction_s.Head = 5

refwaterlevel_s.WaterSegments[-1].TimeDependency = refwaterlevel_s.WaterSegments[-1].TimeDependency.timedependent
refwaterlevel_s.WaterSegments[-1].HeadFunction = flowfunction_s

# Changes the mode, define phases
g_i.gotostages()
phases_s = [g_i.phase(g_i.Phases[i]) for i in range(3)]
phases_s[1].TimeInterval = 5

waterlevel_s = g_i.createreachedwl(refwaterlevel_s, phases_s[2])
print(waterlevel_s)
```

---

## INPUT: createreachedwlandcontinue

# Python wrapper commands [CREATEREACHEDWLANDCONTINUE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## createreachedwlandcontinue
Creates a new water level at the position reached at the end of the previous phase. The location of the water level in the current phase will change from that point on according to the flow function assigned to the original water level in the previous phase.

```python
s_i.new()
```

```python
# Alternative 1
# Creates a borehole, soil layer
borehole_g = g_i.borehole(0)
g_i.soillayer(10)

# Changes the mode, adds a waterlevel and assigns a head function
g_i.gotoflow()
refwaterlevel_s = g_i.waterlevel((0, 4), (10, 4))
flowfunction_s = g_i.headfunction()
flowfunction_s.Signal = flowfunction_s.Signal.linear
flowfunction_s.Time = 5
flowfunction_s.Head = 5

refwaterlevel_s.WaterSegments[-1].TimeDependency = refwaterlevel_s.WaterSegments[-1].TimeDependency.timedependent
refwaterlevel_s.WaterSegments[-1].HeadFunction = flowfunction_s

# Changes the mode, define phases
g_i.gotostages()
phases_s = [g_i.phase(g_i.Phases[i]) for i in range(3)]
phases_s[1].TimeInterval = 5

waterlevel_s = g_i.createreachedwlandcontinue(refwaterlevel_s, phases_s[2])
print(waterlevel_s)
```

---

## INPUT: cutpoly

# Python wrapper commands [CUTPOLY]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## cutpoly
Cuts/divides polygons.

```python
s_i.new()
```

```python
# Alternative 1
# Example 1
g_i.polygon((0, 0), (0, 2), (2, 2), (2, 0))
print(g_i.cutpoly((0.5, 0), (0.5, 3)))

# Example 2
point_g = g_i.point(0, 1)
print(g_i.cutpoly(point_g, (4, 1)))

# Example 3
point1_g, point2_g = g_i.point((1, 0), (1, 2))
print(g_i.cutpoly(point1_g, point2_g))

# Example 4
point_g = g_i.point(1.5, 0)
print(g_i.cutpoly(point_g, (1.5, 1), (2, 2)))
```

---

## INPUT: deactivate

# Python wrapper commands [DEACTIVATE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## deactivate
Deactivates features.

```python
s_i.new()
```

```python
# Alternative 1
# Deactivates a feature in one or more phases.

# Example 1
# Creates a borehole, two soil layers
borehole_g = g_i.borehole(0)
g_i.soillayer(5)
g_i.soillayer(10)
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((1, 1), (2, 2))[-1]

# Changes the mode, define the phases
g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
phase2_s = g_i.phase(phase0_s)
soil_s = g_i.Soils[-1]

print(soil_s.deactivate(phase0_s, phase1_s))

# Example 2
line_s = g_i.Lines[-1]

print(line_s.deactivate(phase0_s, phase2_s))
```

```python
s_i.new()
```

```python
# Alternative 2
# Deactivates one or more activatable objects in one or more phases.

# Example 1
# Creates a borehole, two soil layers
borehole_g = g_i.borehole(0)
g_i.soillayer(5)
g_i.soillayer(10)

# Changes the mode, define the phases
g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
soils_s = g_i.Soils

print(g_i.deactivate((soils_s[-1], soils_s[-2]), (phase0_s, phase1_s)))

# Example 2
phase2_s = g_i.phase(phase1_s)

print(g_i.deactivate((soils_s[-1], soils_s[-2]), phase1_s, phase2_s))
```

---

## INPUT: delete

# Python wrapper commands [DELETE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## delete
Deletes objects.

```python
s_i.new()
```

```python
# Alternative 1
# Deletes one or more objects.

# Creates multiple objects, the first one is the Polygon object ([0])
polygon_g = g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))[0] 
point_g = g_i.point(1, 1)
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((2, 2), (3, 3))[-1] 

print(g_i.delete(polygon_g, line_g, point_g))
```

```python
# Alternative 2
# Deletes a phase.

g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)

print(g_i.delete(phase1_s))
```

```python
s_i.new()
```

```python
# Alternative 3
# Deletes one or more features.

# Creates multiple objects, the last one is the Plate/Geogrid feature object ([-1])
plate_g = g_i.plate((0, 0), (0, 2))[-1] 
geogrid_g = g_i.geogrid((1, 4), (6, 5))[-1]

print(g_i.delete(plate_g, geogrid_g))
```

```python
# Alternative 4
# Deletes one or more materials.

material_i = g_i.soilmat()
g_i.delete(material_i)
```

```python
# Alternative 5
# Deletes a segment of a polycurve.

# Creates multiple objects, the first one is the Polycurve object ([0])
polycurve_g = g_i.polycurve((0, 0), "line", 0, 2, "arc", 45, 90, 1)[0]
g_i.delete(polycurve_g.Segments[-1])
```

```python
s_i.new()
```

```python
# Alternative 6
# Deletes a load factor label.

loadfactorlabel_i = g_i.loadfactorlabel()
g_i.delete(loadfactorlabel_i)
```

```python
# Alternative 7
# Deletes a material factor label.

materialfactorlabel_i = g_i.materialfactorlabel()
g_i.delete(materialfactorlabel_i)
```

```python
# Alternative 8
# Deletes a design approach.

designapproach_i = g_i.designapproach()
g_i.delete(designapproach_i)
```

```python
s_i.new()
```

```python
# Alternative 9
# Deletes a field data object.

fielddata_s = g_i.importfielddata("C:/PLAXIS2D/test1.CPT")
g_i.delete(fielddata_s)
```

```python
s_i.new()
```

```python
# Alternative 10
# Deletes one or more sub sections of a tunnel cross section.

# Creates a tunnel, define the CrossSection and add reinforcement 
tunnel_g = g_i.tunnel(0, 0)
tunnel_g.CrossSection.WholeHalfMode = tunnel_g.CrossSection.WholeHalfMode.right
segment1_g = tunnel_g.CrossSection.add()
segment2_g = tunnel_g.CrossSection.add()
segment2_g.SegmentType = segment2_g.SegmentType.arc
tunnel_g.CrossSection.extendtosymmetryaxis()
polycurvechain_g, rockbolt_g = g_i.rockboltsperpendicular(tunnel_g.SliceSegments[-1])

g_i.delete(polycurvechain_g)
```

```python
# Alternative 11
# Deletes a borehole.
borehole_g = g_i.borehole(0)
g_i.delete(borehole_g)
```

```python
s_i.new()
```

```python
# Alternative 12
# Deletes a soil layer.

borehole_g = g_i.borehole(0)
g_i.soillayer(10)
soillayer_g = g_i.Soillayers[-1]

g_i.delete(soillayer_g)
```

```python
# Alternative 13
# Deletes a multiplier.

loadmultiplier_g = g_i.loadmultiplier()
g_i.delete(loadmultiplier_g)
```

```python
s_i.new()
```

```python
# Alternative 14
# Deletes a head or discharge function.

flowfunction_g = g_i.headfunction()
# g_i.delete(flowfunction_g)
```

```python
# Alternative 15
# Deletes a row from an advanced table.

flowfunction_g = g_i.headfunction()
flowfunction_g.Signal = "Table"

for i in range(10):
    flowfunction_g.Table.add(i, i+1)

g_i.delete(flowfunction_g.Table, 2)
```

```python
s_i.new()
```

```python
# Alternative 16
# Deletes one or more water levels.
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))

g_i.gotoflow()
waterlevel1_s = g_i.waterlevel((0, 0), (1, 2))
waterlevel2_s = g_i.waterlevel((2, 2), (7, 1))

g_i.delete(waterlevel1_s, waterlevel2_s)
```

---

## INPUT: deletepoint

# Python wrapper commands [DELETEPOINT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## deletepoint
Deletes a point of a polygon or water level.

```python
s_i.new()
```

```python
# Alternative 1
# Creates multiple objects, the first one is the Polygon object ([0])
polygon_g = g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))[0]

polygon_g.deletepoint(1)
```

```python
s_i.new()
```

```python
# Alternative 2
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))

g_i.gotoflow()
waterlevel_s = g_i.waterlevel((1, 2), (2, 2), (3, 2))

waterlevel_s.deletepoint(1)
```

---

## INPUT: delruntimetoggle

# Python wrapper commands [DELRUNTIMETOGGLE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## delruntimetoggle
Removes a runtime toggle.

```python
s_i.new()
```

```python
# Alternative 1
g_i.delruntimetoggle("DISPLAY_BUILD_IN_CAPTION")
```

---

## INPUT: designapproach

# Python wrapper commands [DESIGNAPPROACH]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## designapproach 
Adds design approach.

```python
s_i.new()
```

```python
# Alternative 1
designapproach_g = g_i.designapproach()
print(designapproach_g)
```

---

## INPUT: dischargefunction

# Python wrapper commands [DISCHARGEFUNCTION]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## dischargefunction 
Adds a discharge function

```python
s_i.new()
```

```python
# Alternative 1
for i in range(3):
    g_i.dischargefunction()

print(g_i.tabulate(g_i.FlowFunctions))

# Obtain Signal property value assigned for all discharge functions in a list and display them
dischargefunctions_signal = g_i.FlowFunctions.Signal.value
print(f'Discharge functions signal: {dischargefunctions_signal}')
```

---

## INPUT: displmultiplier

# Python wrapper commands [DISPLMULTIPLIER]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## displmultiplier 
Adds a displacement multiplier.

```python
s_i.new()
```

```python
# Alternative 1

for i in range(3):
    g_i.displmultiplier()

print(g_i.tabulate(g_i.DynamicMultipliers))

# Obtain Signal property value assigned for all discharge functions in a list and display them
displmultipliers_signal = g_i.DynamicMultipliers.Signal.value
print(f'Displacement multipliers signal: {displmultipliers_signal}')
```

---

## INPUT: drain

# Python wrapper commands [DRAIN]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## drain
Adds drain features to lines.

```python
s_i.new()
```

```python
# Alternative 1
# Adds drain features to one or more existing lines in the geometry.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((2, 2), (3, 3))[-1]
drain_g = g_i.drain(line_g)
print(drain_g)

# Example 2
# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((0, 2), (2, 2))[-1]
line2_g = g_i.line((2, 2), (2, 0))[-1]
drains_g = g_i.drain(line1_g, line2_g)
print(drains_g)
```

```python
s_i.new()
```

```python
# Alternative 2
# Creates a line between two points (which may either exist, or will be created) and add a drain feature to it.

# Example 1
# Creates multiple objects, the last one is the Drain object ([-1])
point_g = g_i.point(0, 0)
drain_g = g_i.drain(point_g, (5, 6))[-1]
print(drain_g)

# Example 2
points_g = g_i.point((1, 1), (1, 4))
line_g, drain_g = g_i.drain(points_g[-2], points_g[-1])
print(drain_g)

# Example 3
# Creates multiple objects, the last one is the Drain object ([-1])
drain_g = g_i.drain((5, 5), (5, 2))[-1]
print(drain_g)
```

```python
s_i.new()
```

```python
# Alternative 3
# Creates lines between three or more points (which may either exist, or will be created) and add drain features to them.

points_g = g_i.point((1, 1), (4, 4))
res = g_i.drain(points_g[-2], (2, 3), points_g[-1])
drains_g = [item for item in res if item._plx_type == 'Drain']
print(drains_g)
```

```python
s_i.new()
```

```python
# Alternative 4
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect
# to the xy-plane and a length or a vector describing the direction and a length and add drain features to them.

# Example 1
# Creates multiple objects, the last one is the Drain object ([-1])
drain_g = g_i.drain((1, 2), "relative", (3, 4))[-1]
print(drain_g)

# Example 2
point_g = (1, 2)
res = g_i.drain(point_g, "relative", (3, 4), (-5, -9), "angles", 30, 16)
drains_g = [item for item in res if item._plx_type == 'Drain']
print(drains_g)

# Example 3
res = g_i.drain((1, 2), "angles", 45, 10, "absolute", (4, 5))
drains_g = [item for item in res if item._plx_type == 'Drain']
print(drains_g)

# Obtain Behaviour property value assigned for all drains in a list and display them
drains_behaviour= g_i.Drains.Behaviour.value
print(f'Drains Behaviour property: {drains_behaviour}')
```

```python
s_i.new()
```

```python
# Alternative 5
# Adds drain features to one or more existing lines in the geometry and directly set their properties.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((2, 2), (3, 3))[-1]
drain_g = g_i.drain(line_g, "h", 1.2)
print(drain_g)

# Example 2
line1_g = g_i.line((2, 4), (3, 4))[-1]
line2_g = g_i.line((0, 2), (1, 2))[-1]
drains_g = g_i.drain(line1_g, line2_g, "h", 1.2)
print(drains_g)
```

```python
s_i.new()
```

```python
# Alternative 6
# Creates a line between two points (which may either exist, or will be created), add a drain feature to it and directly set its properties.

# Creates multiple objects, the last one is the Drain object ([-1])
point_g = g_i.point(1, 1)
drain_g = g_i.drain(point_g, (5, 6), "h", 1.2)[-1]
print(drain_g)
```

```python
s_i.new()
```

```python
# Alternative 7
# Creates lines between three or more points (which may either exist, or will be created), add drain features to them and directly set their properties.

point1_g, point2_g = g_i.point((1, 1), (8, 9))
res = g_i.drain(point1_g, (5.1, 6.4), point2_g, "h", 1.2)
drains_g = [item for item in res if item._plx_type == 'Drain']
print(drains_g)
```

```python
# Alternative 8
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect 
# to the xy-plane and a length or a vector describing the direction and a length, add drain features to them and directly set their properties.

# Creates multiple objects, the last one is the Drain object ([-1])
drain_g = g_i.drain((1, 2), "relative", (3, 4), "h", 1.2)[-1]
print(drain_g)
```

---

## INPUT: dump

# Python wrapper commands [DUMP]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## dump
Displays the details of an object.

```python
s_i.new()
```

```python
# Alternative 1
# Displays extended details of the project.

print(g_i.dump())
```

```python
# Alternative 2
# Displays details of a specified object.

# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((2, 2), (3, 3))[-1]
print(line_g.dump())
```

```python
# Alternative 3
# Displays the details of one or more objects.

point1_g, point2_g = g_i.point((2, 4), (4, 7))
print(g_i.dump(point1_g, point2_g))
```

```python
# Alternative 4
# Displays details of objects in the list of objects.

points_g = g_i.Points
print(g_i.dump(points_g))
```

---

## INPUT: dumpboreholes

# Python wrapper commands [DUMPBOREHOLES]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## dumpboreholes
Displays a list of all boreholes.

```python
s_i.new()
```

```python
# Alternative 1
g_i.borehole(0)
g_i.borehole(1)
g_i.borehole(2)
g_i.borehole(3)
g_i.borehole(4)

print(g_i.dumpboreholes())
```

---

## INPUT: dumpcutobjects

# Python wrapper commands [DUMPCUTOBJECTS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## dumpcutobjects
Displays a list of all cut objects.

```python
s_i.new()
```

```python
# Alternative 1
g_i.polygon((0, 7), (10, 7), (10, 0), (0, 0))
g_i.plate((0, 5), (10, 5))
g_i.plate((5, 7), (5, 0))

g_i.gotomesh()

print(g_i.dumpcutobjects())
```

---

## INPUT: dumpfixedendanchors

# Python wrapper commands [DUMPFIXEDENDANCHORS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## dumpfixedendanchors
Displays a list of all fixed-end anchors.

```python
s_i.new()
```

```python
# Alternative 1

g_i.fixedendanchor((1, 3), (2, 5), (4, 4))

print(g_i.dumpfixedendanchors())
```

---

## INPUT: dumpgeogrids

# Python wrapper commands [DUMPGEOGRIDS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## dumpgeogrids
Displays a list of all geogrids.

```python
s_i.new()
```

```python
# Alternative 1
g_i.geogrid((0, 0), (1, 1), (1, 0), (2, 0))

print(g_i.dumpgeogrids())
```

---

## INPUT: dumpgroups

# Python wrapper commands [DUMPGROUPS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## dumpgroups
Displays a list of all created groups

```python
s_i.new()
```

```python
# Alternative 1

# Creates Polygon and Soil objects, the first one is the Polygon object
point1_g, point2_g = g_i.point((1, 1), (2, 2))
polygon_g = g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))[0] 

# Displays a list of all created groups
group_g = g_i.group(polygon_g, point1_g, point2_g)

print(g_i.dumpgroups())
```

---

## INPUT: dumplinedispls

# Python wrapper commands [DUMPLINEDISPLS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## dumplinedispls
Displays a list of all line prescribed displacements.

```python
s_i.new()
```

```python
# Alternative 1
g_i.linedispl((0, 0), (3, 4), (5, 5), (6, 0))

print(g_i.dumplinedispls())
```

---

## INPUT: dumplineloads

# Python wrapper commands [DUMPLINELOADS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## dumplineloads
Displays a list of all line loads.

```python
s_i.new()
```

```python
# Alternative 1
g_i.lineload((1, 2), (3, 4), (5, 7))

print(g_i.dumplineloads())
```

---

## INPUT: dumplines

# Python wrapper commands [DUMPLINES]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## dumplines
Displays a list of all lines.

```python
s_i.new()
```

```python
# Alternative 1
g_i.line((1, 0), (9, 4), (8, 6), (10, 0))

print(g_i.dumplines())
```

---

## INPUT: dumpmaterials

# Python wrapper commands [DUMPMATERIALS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## dumpmaterials
Displays a list of all materials.

```python
s_i.new()
```

```python
# Alternative 1
g_i.anchormat("MaterialName", "AnchorMat")
g_i.soilmat("MaterialName", "SoilMat")
g_i.embeddedbeammat("MaterialName", "BeamMat")


print(g_i.dumpmaterials())
```

---

## INPUT: dumpmeshes

# Python wrapper commands [DUMPMESHES]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## dumpmeshes
Displays the details of the mesh of a cut object.

```python
s_i.new()
```

```python
# Alternative 1
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))

g_i.gotomesh()
g_i.mesh()
polygon_s = g_i.Polygons[-1]

print(polygon_s.dumpmeshes())
```

---

## INPUT: dumpn2nanchors

# Python wrapper commands [DUMPN2NANCHORS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## dumpn2nanchors
Displays a list of all node-to-node anchors.

```python
s_i.new()
```

```python
# Alternative 1
g_i.n2nanchor((0, 0), (1, 2), (3, 4), (5, 0))

print(g_i.dumpn2nanchors())
```

---

## INPUT: dumpnegativeinterfaces

# Python wrapper commands [DUMPNEGATIVEINTERFACES]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## dumpnegativeinterfaces
Displays a list of all negative interfaces.

```python
s_i.new()
```

```python
# Alternative 1
g_i.neginterface((0, 0), (0, 1), (1, 1))

print(g_i.dumpnegativeinterfaces())
```

---

## INPUT: dumpphases

# Python wrapper commands [DUMPPHASES]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## dumpphases
Displays a list of all phases.

```python
s_i.new()
```

```python
# Alternative 1
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))

g_i.gotostages()

for i in range(5):
    g_i.phase(g_i.Phases[0])

print(g_i.dumpphases())
```

---

## INPUT: dumppiles

# Python wrapper commands [DUMPPILES]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## dumppiles
Displays a list of all embedded piles.

```python
s_i.new()
```

```python
# Alternative 1
# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((0, 2), (2, 2))[-1]
line2_g = g_i.line((2, 2), (2, 0))[-1]
embeddedpilerows_g = g_i.embeddedpilerow(line1_g, line2_g)

print(g_i.dumppiles())
```

---

## INPUT: dumpplates

# Python wrapper commands [DUMPPLATES]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## dumpplates
Displays a list of all plates.

```python
s_i.new()
```

```python
# Alternative 1
g_i.plate((0, 0), (1, 1), (2, 1), (3, 0))

print(g_i.dumpplates())
```

---

## INPUT: dumppointdispls

# Python wrapper commands [DUMPPOINTDISPLS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## dumppointdispls
Displays a list of all point prescribed displacements.

```python
s_i.new()
```

```python
# Alternative 1
g_i.pointdispl((0, 0), (0, 1), (1, 1), (2, 0))

print(g_i.dumppointdispls())
```

---

## INPUT: dumppointloads

# Python wrapper commands [DUMPPOINTLOADS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## dumppointloads
Displays a list of all point loads.

```python
s_i.new()
```

```python
# Alternative 1
g_i.pointload((0, 0), (0, 1), (1, 1), (2, 0))

print(g_i.dumppointloads())
```

---

## INPUT: dumppoints

# Python wrapper commands [DUMPPOINTS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## dumppoints
Displays a list of all points.

```python
s_i.new()
```

```python
# Alternative 1
g_i.point((1, 1), (2, 2), (3, 1), (4, 0))

print(g_i.dumppoints())
```

---

## INPUT: dumppolygons

# Python wrapper commands [DUMPPOLYGONS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## dumppolygons
Displays a list of all polygons.

```python
s_i.new()
```

```python
# Alternative 1
# Creates Polygon and Soil objects, the first one is the Polygon object
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))
g_i.polygon((3, 2), (4, 5), (10, 11))

print(g_i.dumppolygons())
```

---

## INPUT: dumppositiveinterfaces

# Python wrapper commands [DUMPPOSITIVEINTERFACES]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## dumppositiveinterfaces
Displays a list of all positive interfaces.

```python
s_i.new()
```

```python
# Alternative 1
g_i.posinterface((0, 0), (0, 1), (1, 1))

print(g_i.dumppositiveinterfaces())
```

---

## INPUT: dumpsoillayers

# Python wrapper commands [DUMPSOILLAYERS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## dumpsoillayers
Displays a list of all soil layers.

```python
s_i.new()
```

```python
# Alternative 1
g_i.borehole(0)
g_i.soillayer(1)
g_i.soillayer(2)
g_i.soillayer(3)

print(g_i.dumpsoillayers())
```

---

## INPUT: duplicate

# Python wrapper commands [DUPLICATE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## duplicate
Duplicates water levels.

```python
s_i.new()
```

```python
# Alternative 1
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))

g_i.gotoflow()
waterlevel1_s = g_i.waterlevel((1, 4), (2, 4))
waterlevel2_s = g_i.waterlevel((1, 4), (2, 4))
waterlevels = g_i.duplicate(waterlevel1_s, waterlevel2_s)
print(waterlevels)
```

---

## INPUT: echo

# Python wrapper commands [ECHO]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## echo
Displays the details of an object.

```python
s_i.new()
```

```python
# Alternative 1
# Displays extended details of the project.

print(g_i.echo())
```

```python
# Alternative 2
# Displays details of a specified object.

# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((2, 2), (3, 3))[-1]
print(line_g.echo())
```

```python
# Alternative 3
# Displays details of one or more specified objects.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((2, 4), (3, 4))[-1]
line2_g = g_i.line((0, 2), (1, 2))[-1]

print(g_i.echo(line1_g, line2_g.Length))

# Example 2
point1_g, point2_g = g_i.point((3, 4), (5, 7))

print(g_i.echo(point1_g.x, point2_g.y))
```

```python
# Alternative 4
# Displays details of a list of items

points_g = g_i.Points
print(g_i.echo(points_g))
```

```python
s_i.new()
```

```python
# Alternative 4
# Displays extended details of the material in a specified phase.

g_i.polygon((0, 0),(5, 0),(5, 5), (0, 5))
material_i = g_i.soilmat()

g_i.gotostages()
phase1_s = g_i.phase(g_i.Phases[0])

print(g_i.echo(material_i, phase1_s))
```

---

## INPUT: echotunnelvalidation

# Python wrapper commands [ECHOTUNNELVALIDATION]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## echotunnelvalidation
Displays the errors, warnings and tips related to cross-section, properties, trajectory and sequencing of a tunnel in the tunnel designer.

```python
s_i.new()
```

```python
# Alternative 1
tunnel_g = g_i.tunnel(0, 0)
tunnel_g.CrossSection.WholeHalfMode = tunnel_g.CrossSection.WholeHalfMode.right
segment1_g = tunnel_g.CrossSection.add()
print(g_i.echotunnelvalidation(tunnel_g))
```

---

## INPUT: embeddedbeammat

# Python wrapper commands [EMBEDDEDBEAMMAT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## embeddedbeammat
Creates an embedded beam material set.

```python
s_i.new()
```

```python
# Alternative 1
g_i.embeddedbeammat()
```

---

## INPUT: embeddedbeamrow

# Python wrapper commands [EMBEDDEDBEAMROW]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## embeddedbeamrow
Adds embedded beam row features to lines.

```python
s_i.new()
```

```python
# Alternative 1
# Adds embedded beam row features to one or more existing lines in the geometry.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((0, 0), (1, 1))[-1]
embeddedbeamrow_g = g_i.embeddedbeamrow(line_g)
print(embeddedbeamrow_g)

# Example 2
# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((0, 2), (2, 2))[-1]
line2_g = g_i.line((2, 2), (2, 0))[-1]
embeddedbeamrows_g = g_i.embeddedbeamrow(line1_g, line2_g)
print(embeddedbeamrows_g)
```

```python
s_i.new()
```

```python
# Alternative 2
# Creates a line between two points (which may either exist, or will be created) and add a embeddedbeamrow feature to it.

# Example 1
# Creates multiple objects, the last one is the EmbeddedBeamRow object ([-1])
point_g = g_i.point(0, 0)
embeddedbeamrow_g = g_i.embeddedbeamrow(point_g, (5, 6))[-1] 
print(embeddedbeamrow_g)

# Example 2

points_g = g_i.point((1, 1), (1, 4))
line_g, embeddedbeamrow_g = g_i.embeddedbeamrow(points_g[-2], points_g[-1])
print(embeddedbeamrow_g)

# Example 3
# Creates multiple objects, the last one is the EmbeddedBeamRow object ([-1])
embeddedbeamrow_g = g_i.embeddedbeamrow((5, 5), (5, 2))[-1]
print(embeddedbeamrow_g)
```

```python
# Alternative 3
# Creates lines between three or more points (which may either exist, or will be created) and add embedded beam row features to them.

points_g = g_i.point((1, 1), (4, 4))
res = g_i.embeddedbeamrow(points_g[-2], (2, 3), points_g[-1])
embeddedbeamrows_g = [item for item in res if item._plx_type == 'EmbeddedBeamRow']
print(embeddedbeamrows_g)
```

```python
s_i.new()
```

```python
# Alternative 4
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect 
# to the xy-plane and a length or a vector describing the direction and a length and add embedded beam row features to them.

# Example 1
# Creates multiple objects, the last one is the EmbeddedBeamRow object ([-1])
embeddedbeamrow_g = g_i.embeddedbeamrow((1, 2), "relative", (3, 4))[-1]
print(embeddedbeamrow_g)

# Example 2
point_g = (1, 2)
res = g_i.embeddedbeamrow(point_g, "relative", (3, 4), (-5, -9), "angles", 30, 16)
embeddedbeamrows_g = [item for item in res if item._plx_type == 'EmbeddedBeamRow']
print(embeddedbeamrows_g)

# Example 3
res = g_i.embeddedbeamrow((1, 2), "angles", 45, 10, "absolute", (4, 5))
embeddedbeamrows_g = [item for item in res if item._plx_type == 'EmbeddedBeamRow']
print(embeddedbeamrows_g)

# Obtain Connection property value assigned for all embedded beam rows in a list and display them
embeddedbeam_rows_connection = g_i.EmbeddedBeamRows.Connection.value
print(f'Embedded Beam rows connection property: {embeddedbeam_rows_connection}')
```

```python
s_i.new()
```

```python
# Alternative 5
# Adds embedded beam row features to one or more existing lines in the geometry and directly set their properties.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((2, 2), (3, 3))[-1] 
material_i = g_i.embeddedbeammat()
embeddedbeamrow_g = g_i.embeddedbeamrow(line_g, "Material", material_i)
print(embeddedbeamrow_g)

# Example 2
# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((2, 4), (3, 4))[-1]
line2_g = g_i.line((0, 2), (1, 2))[-1]
material_i = g_i.embeddedbeammat()
embeddedbeamrows_g = g_i.embeddedbeamrow((line1_g, line2_g), "Material", material_i)
print(embeddedbeamrows_g)
```

```python
s_i.new()
```

```python
# Alternative 6
# Creates a line between two points (which may either exist, or will be created), add a embeddedbeamrow feature to it and directly set its properties.

# Creates multiple objects, the last one is the EmbeddedBeamRow object ([-1])
point_g = g_i.point(1, 1)
material_i = g_i.embeddedbeammat()
embeddedbeamrow_g = g_i.embeddedbeamrow(point_g, (5, 6), "Material", material_i)[-1]
print(embeddedbeamrow_g)
```

```python
s_i.new()
```

```python
# Alternative 7
# Creates lines between three or more points (which may either exist, or will be created), add embedded beam row features to them and directly set their properties.


point1_g, point2_g = g_i.point((1, 1), (8, 9))
material_i = g_i.embeddedbeammat()
res = g_i.embeddedbeamrow(point1_g, (5.1, 6.4), point2_g, "Material", material_i)
embeddedbeamrows_g = [item for item in res if item._plx_type == 'EmbeddedBeamRow']
print(embeddedbeamrows_g)
```

```python
s_i.new()
```

```python
# Alternative 8
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect 
# to the xy-plane and a length or a vector describing the direction and a length, add embedded beam row features to them and directly set their properties.

# Creates multiple objects, the last one is the EmbeddedBeamRow object ([-1])
material_i = g_i.embeddedbeammat()
embeddedbeamrow_g = g_i.embeddedbeamrow((1, 2), "relative", (3, 4), "Material", material_i)[-1]
print(embeddedbeamrow_g)
```

---

## INPUT: embeddedpilemat

# Python wrapper commands [EMBEDDEDPILEMAT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## embeddedpilemat
Creates an embedded pile material set.

```python
s_i.new()
```

```python
# Alternative 1
g_i.embeddedpilemat()
```

---

## INPUT: embeddedpilerow

# Python wrapper commands [EMBEDDEDPILEROW]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## embeddedpilerow
Adds embedded beam row features to lines.

```python
s_i.new()
```

```python
# Alternative 1
# Adds embedded beam row features to one or more existing lines in the geometry.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((0, 0), (1, 1))[-1]
embeddedpilerow_g = g_i.embeddedpilerow(line_g)
print(embeddedpilerow_g)

# Example 2
# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((0, 2), (2, 2))[-1]
line2_g = g_i.line((2, 2), (2, 0))[-1]
embeddedpilerows_g = g_i.embeddedpilerow(line1_g, line2_g)
print(embeddedpilerows_g)
```

```python
s_i.new()
```

```python
# Alternative 2
# Creates a line between two points (which may either exist, or will be created) and add a embeddedpilerow feature to it.

# Example 1
# Creates multiple objects, the last one is the EmbeddedPileRow object ([-1])
point_g = g_i.point(0, 0)
embeddedpilerow_g = g_i.embeddedpilerow(point_g, (5, 6))[-1] 
print(embeddedpilerow_g)

# Example 2

points_g = g_i.point((1, 1), (1, 4))
line_g, embeddedpilerow_g = g_i.embeddedpilerow(points_g[-2], points_g[-1])
print(embeddedpilerow_g)

# Example 3
# Creates multiple objects, the last one is the EmbeddedPileRow object ([-1])
embeddedpilerow_g = g_i.embeddedpilerow((5, 5), (5, 2))[-1]
print(embeddedpilerow_g)
```

```python
# Alternative 3
# Creates lines between three or more points (which may either exist, or will be created) and add embedded beam row features to them.

points_g = g_i.point((1, 1), (4, 4))
res = g_i.embeddedpilerow(points_g[-2], (2, 3), points_g[-1])
embeddedpilerows_g = [item for item in res if item._plx_type == 'EmbeddedBeamRow']
print(embeddedpilerows_g)
```

```python
s_i.new()
```

```python
# Alternative 4
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect 
# to the xy-plane and a length or a vector describing the direction and a length and add embedded beam row features to them.

# Example 1
# Creates multiple objects, the last one is the EmbeddedPileRow object ([-1])
embeddedpilerow_g = g_i.embeddedpilerow((1, 2), "relative", (3, 4))[-1]
print(embeddedpilerow_g)

# Example 2
point_g = (1, 2)
res = g_i.embeddedpilerow(point_g, "relative", (3, 4), (-5, -9), "angles", 30, 16)
embeddedpilerows_g = [item for item in res if item._plx_type == 'EmbeddedBeamRow']
print(embeddedpilerows_g)

# Example 3
res = g_i.embeddedpilerow((1, 2), "angles", 45, 10, "absolute", (4, 5))
embeddedpilerows_g = [item for item in res if item._plx_type == 'EmbeddedBeamRow']
print(embeddedpilerows_g)
```

```python
s_i.new()
```

```python
# Alternative 5
# Adds embedded beam row features to one or more existing lines in the geometry and directly set their properties.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((2, 2), (3, 3))[-1] 
material_i = g_i.embeddedpilemat()
embeddedpilerow_g = g_i.embeddedpilerow(line_g, "Material", material_i)
print(embeddedpilerow_g)

# Example 2
# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((2, 4), (3, 4))[-1]
line2_g = g_i.line((0, 2), (1, 2))[-1]
material_i = g_i.embeddedpilemat()
embeddedpilerows_g = g_i.embeddedpilerow((line1_g, line2_g), "Material", material_i)
print(embeddedpilerows_g)
```

```python
s_i.new()
```

```python
# Alternative 6
# Creates a line between two points (which may either exist, or will be created), add a embeddedpilerow feature to it and directly set its properties.

# Creates multiple objects, the last one is the EmbeddedPileRow object ([-1])
point_g = g_i.point(1, 1)
material_i = g_i.embeddedpilemat()
embeddedpilerow_g = g_i.embeddedpilerow(point_g, (5, 6), "Material", material_i)[-1]
print(embeddedpilerow_g)
```

```python
s_i.new()
```

```python
# Alternative 7
# Creates lines between three or more points (which may either exist, or will be created), add embedded beam row features to them and directly set their properties.


point1_g, point2_g = g_i.point((1, 1), (8, 9))
material_i = g_i.embeddedpilemat()
res = g_i.embeddedpilerow(point1_g, (5.1, 6.4), point2_g, "Material", material_i)
embeddedpilerows_g = [item for item in res if item._plx_type == 'EmbeddedBeamRow']
print(embeddedpilerows_g)
```

```python
s_i.new()
```

```python
# Alternative 8
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect 
# to the xy-plane and a length or a vector describing the direction and a length, add embedded beam row features to them and directly set their properties.

# Creates multiple objects, the last one is the EmbeddedPileRow object ([-1])
material_i = g_i.embeddedpilemat()
embeddedpilerow_g = g_i.embeddedpilerow((1, 2), "relative", (3, 4), "Material", material_i)[-1]
print(embeddedpilerow_g)
```

---

## INPUT: export

# Python wrapper commands [EXPORT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## export 
Exports 2D models, structural entities, geometries, cutobjects, as CAD file formats (.step, .stp, .dxf, .brep)

```python
s_i.new()
```

```python
# Alternative 1
# Exports a defined 2D model to a specified location in a specified file format

g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))
g_i.export("C:\PLAXIS2D\CADgeometry.step")
```

```python
# Alternative 2
# Exports selected geometric objects to a specified location in a specified file format.

# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((2, 4), (3, 4))[-1]
line2_g = g_i.line((0, 2), (1, 2))[-1]

g_i.export("C:\data\CADgeometry.dxf", line1_g)
```

---

## INPUT: extendtosymmetryaxis

# Python wrapper commands [EXTENDTOSYMMETRYAXIS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## extendtosymmetryaxis 
Extends a polycurve to its symmetry axis by adding a new segment.

```python
s_i.new()
```

```python
# Alternative 1
# Creates multiple objects, the first one is the Polycurve object ([0])
polycurve_g = g_i.polycurve((4, 5), "line", 0, 2, "arc", 45, 90, 3)[0]

polycurve_g.extendtosymmetryaxis()
```

---

## INPUT: fieldstress

# Python wrapper commands [FIELDSTRESS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## fieldstress 
Adds field stress feature to soil clusters.

```python
s_i.new()
```

```python
# Alternative 1
# Adds field stress feature to soil clusters

# Adds a borehole and three soil layers
g_i.borehole(0)
g_i.soillayer(1)
g_i.soillayer(2)
g_i.soillayer(3)

soils_g = g_i.Soils

g_i.fieldstress(soils_g[-1], soils_g[-2])
```

```python
# Alternative 2
# Adds field stress feature to soil clusters with specified properties

g_i.fieldstress(soils_g[0], "sig1", 123, "sig2", 456)
```

---

## INPUT: filter

# Python wrapper commands [FILTER]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## filter
Displays a list of specified objects.

```python
s_i.new()
```

```python
# Alternative 1
g_i.soilmat()
g_i.platemat()
g_i.embeddedbeammat()
materials_i = g_i.Materials

print(g_i.filter(materials_i))
```

```python
# Alternative 2
# Displays an object with a specified index from a list of objects.
g_i.point((0, 0), (1, 0), (1, 1), (2, 1))

points_g = g_i.Points
print(g_i.filter(points_g, 3))
```

```python
s_i.new()
```

```python
# Alternative 3
# Displays a number of objects from a specified list of objects starting from a specified object
g_i.line((1, 2), (3, 4), (5, 0), (7, 5), (8, 3))
lines_g = g_i.Lines

print(g_i.filter(lines_g, 1, 3))
```

```python
s_i.new()
```

```python
# Alternative 4
# Displays a list of objects that fulfill a specified criterion.

# Example 1
g_i.point((0, 0), (1, 2), (2, 3), (4, 5), (1, 3))
points_g = g_i.Points

print(g_i.filter(points_g, "x<2"))

# Example 2
g_i.clear()
g_i.platemat()
g_i.anchormat()
g_i.soilmat("MaterialName", "Soil1")
g_i.soilmat("MaterialName", "Soil2")
materials_i = g_i.Materials

print(g_i.filter(materials_i, "SoilMat"))
```

```python
s_i.new()
```

```python
# Alternative 5
# Displays a list of specified staged construction features in a specified phase.
g_i.polygon((0, 0), (0, 4), (5, 4), (5, 0))

g_i.gotostructures()
g_i.embeddedbeamrow((0, 0), (1, 1),(1, 0), (2, 1))

g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)
embeddedbeamrows_s = g_i.EmbeddedBeamRows

print(g_i.filter((embeddedbeamrows_s[-1], embeddedbeamrows_s[-2]), phase1_s))
```

```python
s_i.new()
```

```python
# Alternative 6
# Displays a list of staged construction features with a specified index in a specified phase.
g_i.polygon((0, 0), (0, 4), (5, 4), (5, 0))

g_i.gotostructures()
g_i.embeddedbeamrow((0, 0), (1, 1),(1, 0), (2, 1))

g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)
embeddedbeamrows_s = g_i.EmbeddedBeamRows

print(g_i.filter((embeddedbeamrows_s[-1], embeddedbeamrows_s[-2]), phase1_s, 0))
```

```python
s_i.new()
```

```python
# Alternative 7
# Displays a specified number of staged construction features in a specified phase starting from a specified index.
g_i.polygon((0, 0), (0, 4), (5, 4), (5, 0))

g_i.gotostructures()
g_i.embeddedbeamrow((0, 0), (1, 1),(1, 0), (2, 1))

g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)
embeddedbeamrows_s = g_i.EmbeddedBeamRows

print(g_i.filter(embeddedbeamrows_s, phase1_s, 0, 3))
```

```python
s_i.new()
```

```python
# Alternative 8
# Displays a list of staged construction features that fulfil a condition in a specified phase.
g_i.polygon((0, 0), (0, 4), (5, 4), (5, 0))

g_i.gotostructures()
g_i.embeddedbeamrow((0, 0), (1, 1),(1, 0), (2, 1))

g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)
embeddedbeamrows_s = g_i.EmbeddedBeamRows

embeddedbeamrows_s[-1].activate(phase1_s)

print(g_i.filter(embeddedbeamrows_s, phase1_s, "Active=True"))
```

```python
s_i.new()
```

```python
# Alternative 9
# Displays a list of phases, in which is the specified staged construction feature.
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))

g_i.gotostructures()
g_i.pointload(1, 5)

g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)
phase2_s = g_i.phase(phase1_s)

pointload1_s = g_i.PointLoads[-1]

print(g_i.filter(pointload1_s, phase1_s, phase2_s))
```

```python
s_i.new()
```

```python
# Alternative 10
# Displays a phase with the specified index, in which is the staged construction feature.
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))

g_i.gotostructures()
g_i.pointload(1, 5)

g_i.gotostages()
phases_s = [g_i.phase(g_i.InitialPhase) for i in range(4)]

pointload1_s = g_i.PointLoads[-1]

print(g_i.filter(pointload1_s, phases_s[-1], phases_s[-2], phases_s[-3], 0))
```

```python
s_i.new()
```

```python
# Alternative 11
# Displays a list of phases, in which is the staged construction feature.
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))

g_i.gotostructures()
g_i.pointload(1, 5)

g_i.gotostages()
phases_s = [g_i.phase(g_i.InitialPhase) for i in range(4)]

pointload1_s = g_i.PointLoads[-1]

print(g_i.filter(pointload1_s, phases_s[-1], phases_s[-2], phases_s[-3], 0, 2))
```

```python
s_i.new()
```

```python
# Alternative 12
# Displays phases, in which staged construction features fulfil the specified criterion.
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))

g_i.gotostructures()
g_i.pointload(1, 5)

g_i.gotostages()
phases_s = [g_i.phase(g_i.InitialPhase) for i in range(4)]

pointload1_s = g_i.PointLoads[-1]
pointload1_s.activate(phases_s[-2], phases_s[-1])
print(g_i.filter(pointload1_s, phases_s[-1], phases_s[-2], phases_s[-3], "Active=True"))
```

---

## INPUT: findcutobject

# Python wrapper commands [FINDCUTOBJECT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## findcutobject 
Finds the source entities of the specified cutobject or list of cutobjects in staged construction.

```python
s_i.new()
```

```python
# Alternative 1
# Creates multiple objects, the first one is the Polygon object ([0])
polygon1_g = g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))[0]
polygon2_g = g_i.polygon((0, 0), (0, 2), (2, 2), (2, 0))[0]

g_i.gotostages()
polygon_s = g_i.Polygons[-2]

g_i.findcutobject(polygon_s)
```

---

## INPUT: fixedendanchor

# Python wrapper commands [FIXEDENDANCHOR]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## fixedendanchor 
Adds fixed-end anchor features to points.

```python
s_i.new()
```

```python
# Alternative 1
# Adds fixed-end anchor features to one or more existing points in the geometry.

# Example 1
point_g = g_i.point(1, 1)
fixedendanchor_g = g_i.fixedendanchor(point_g)
print(fixedendanchor_g)

# Example 2
points_g = g_i.point((1, 4), (5, 2), (7, 3))
fixedendanchors_g = g_i.fixedendanchor(points_g[-2], points_g[-1])
print(fixedendanchors_g)
```

```python
# Alternative 2
# Creates a new point and add a fixed-end anchor feature to it.

# Creates multiple objects, the last one is the FixedEndAnchor object ([-1])
fixedendanchor_g = g_i.fixedendanchor((5, 6))[-1] 
print(fixedendanchor_g)
```

```python
# Alternative 3
# Creates several new points and add fixed-end anchor features to them.

res = g_i.fixedendanchor((5, 6), (8, 9))
fixedendanchors_g = [item for item in res if item._plx_type == 'FixedEndAnchor']
print(fixedendanchors_g)
```

```python
s_i.new()
```

```python
# Alternative 4
# Adds fixed-end anchor features to one or more existing points in the geometry and directly set their properties.

# Example 1
point_g = g_i.point(1, 3)
fixedendanchor_g = g_i.fixedendanchor(point_g, "Direction_x", 3, "Direction_y", 7)
print(fixedendanchor_g)

# Example 2
point1_g, point2_g = g_i.point((5, 2), (7, 3))
fixedendanchors_g = g_i.fixedendanchor((point1_g, point2_g), "Direction_x", 3, "Direction_y", 7)
print(fixedendanchors_g)
```

```python
# Alternative 5
# Creates a new point, add a fixed-end anchor feature to it and directly set its properties.

# Creates multiple objects, the last one is the FixedEndAnchor object ([-1])
fixedendanchor_g = g_i.fixedendanchor((5, 6), "Direction_x", 3, "Direction_y", 7)[-1]
print(fixedendanchor_g)
```

```python
# Alternative 6
# Creates several new points, add fixed-end anchor features to them and directly set their properties.

res = g_i.fixedendanchor((5, 6), (8, 9), "Direction_x", 3, "Direction_y", 7)
fixedendanchors_g = [item for item in res if item._plx_type == 'FixedEndAnchor']
print(fixedendanchors_g)

# Obtain Direction_x property value assigned for all fixed end anchors in a list and display them
anchor_direction_x = g_i.FixedEndAnchors.Direction_x.value
print(f'FixedEndAnchors Direction_x property: {anchor_direction_x}')
```

---

## INPUT: generatefromfielddata

# Python wrapper commands [GENERATEFROMFIELDDATA]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## generatefromfielddata
Generates the soil stratigraphy of a borehole based on assigned field data.

```python
s_i.new()
```

```python
# Alternative 1
borehole_g = g_i.borehole(0)
fielddata_g = g_i.importfielddata(r"C:\PLAXIS2D\test1.CPT")
borehole_g.FieldData = fielddata_g
borehole_g.FieldDataInterpreter = "CUR 3 layers"

g_i.generatefromfielddata(borehole_g)
```

---

## INPUT: generateintersectionpoints

# Python wrapper commands [GENERATEINTERSECTIONPOINTS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## generateintersectionpoints
Generates intersection points between two entities.

```python
s_i.new()
```

```python
# Alternative 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((0, 1), (4, 2))[-1]
# Creates multiple objects, the first one is the Polycurve object ([0])
polycurve_g = g_i.polycurve((0, 0), "line", 0, 2, "arc", 45, 90, 3)[0]
g_i.generateintersectionpoints(line_g, polycurve_g)
```

---

## INPUT: generatethicklining

# Python wrapper commands [GENERATETHICKLINING]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## generatethicklining
Generates a thick lining for a tunnel.

```python
s_i.new()
```

```python
# Alternative 1
tunnel_g = g_i.tunnel(0, 0)
tunnel_g.CrossSection.setproperties("ShapeType", "Circular")
tunnel_g.CrossSection.Segments[0].ArcProperties.Radius = 4
g_i.generatethicklining(tunnel_g.CrossSection, 0.1)
```

---

## INPUT: generatetunnel

# Python wrapper commands [GENERATETUNNEL]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## generatetunnel
Generates the geometry representing the tunnel description.

```python
s_i.new()
```

```python
# Alternative 1
tunnel_g = g_i.tunnel(0, 0)
tunnel_g.CrossSection.setproperties("ShapeType", "Circular")
tunnel_g.CrossSection.Segments[0].ArcProperties.Radius = 4

print(g_i.generatetunnel(tunnel_g))
```

---

## INPUT: geogrid

# Python wrapper commands [GEOGRID]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## geogrid
Adds geogrid features to lines.

```python
s_i.new()
```

```python
# Alternative 1
# Adds geogrid features to one or more existing lines in the geometry.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((0, 0), (1, 1))[-1]
geogrid_g = g_i.geogrid(line_g)
print(geogrid_g)

# Example 2
line1_g = g_i.line((0, 2), (2, 2))[-1]
line2_g = g_i.line((2, 2), (2, 0))[-1]
geogrids_g = g_i.geogrid(line1_g, line2_g)
print(geogrids_g)
```

```python
# Alternative 2
# Creates a line between two points (which may either exist, or will be created) and add a geogrid feature to it.

# Example 1
# Creates multiple objects, the last one is the Geogrid object ([-1])
point_g = g_i.point(0, 0)
geogrid_g = g_i.geogrid(point_g, (5, 6))[-1]
print(geogrid_g)

# Example 2
points_g = g_i.point((1, 1), (1, 4))
line_g, geogrid_g = g_i.geogrid(points_g[-2], points_g[-1])
print(geogrid_g)

# Example 3
geogrid_g = g_i.geogrid((5, 5), (5, 2))[-1]
print(geogrid_g)
```

```python
# Alternative 3
# Creates lines between three or more points (which may either exist, or will be created) and add geogrid features to them.

points_g = g_i.point((1, 1), (4, 4))
res = g_i.geogrid(points_g[-2], (2, 3), points_g[-1])
geogrids_g = [item for item in res if item._plx_type == 'Geogrid']
print(geogrids_g)
```

```python
s_i.new()
```

```python
# Alternative 4
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect 
# to the xy-plane and a length or a vector describing the direction and a length and add geogrid features to them.

# Example 1
# Creates multiple objects, the last one is the Geogrid object ([-1])
geogrid_g = g_i.geogrid((1, 2), "relative", (3, 4))[-1]
print(geogrid_g)

# Example 2
point_g = (1, 2)
res = g_i.geogrid(point_g, "relative", (3, 4), (-5, -9), "angles", 30, 16)
geogrids_g = [item for item in res if item._plx_type == 'Geogrid']
print(geogrids_g)

# Example 3
res = g_i.geogrid((1, 2), "angles", 45, 10, "absolute", (4, 5))
geogrids_g = [item for item in res if item._plx_type == 'Geogrid']
print(geogrids_g)

# Obtain ApplyStrengthReduction property value assigned for all geogrids in a list and display them
geogrids_strength_reduction = g_i.Geogrids.ApplyStrengthReduction.value
print(f'Geogrid strength reduction property: {geogrids_strength_reduction}')
```

```python
s_i.new()
```

```python
# Alternative 5
# Adds geogrid features to one or more existing lines in the geometry and directly set their properties.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((2, 2), (3, 3))[-1]
material_i = g_i.geogridmat()
geogrid_g = g_i.geogrid(line_g, "Material", material_i)
print(geogrid_g)

# Example 2
line1_g = g_i.line((2, 4), (3, 4))[-1]
line2_g = g_i.line((0, 2), (1, 2))[-1]
material_i = g_i.geogridmat()
geogrids_g = g_i.geogrid((line1_g, line2_g), "Material", material_i)
print(geogrids_g)
```

```python
# Alternative 6
# Creates a line between two points (which may either exist, or will be created), add a geogrid feature to it and directly set its properties.

# Creates multiple objects, the last one is the Geogrid object ([-1])
point_g = g_i.point(1, 1)
material_i = g_i.geogridmat()
geogrid_g = g_i.geogrid(point_g, (5, 6), "Material", material_i)[-1]
print(geogrid_g)
```

```python
s_i.new()
```

```python
# Alternative 7
# Creates lines between three or more points (which may either exist, or will be created), add geogrid features to them and directly set their properties.

point1_g, point2_g = g_i.point((1, 1), (8, 9))
material_i = g_i.geogridmat()
res = g_i.geogrid(point1_g, (5.1, 6.4), point2_g, "Material", material_i)
geogrids_g = [item for item in res if item._plx_type == 'Geogrid']
print(geogrids_g)
```

```python
# Alternative 8
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect 
# to the xy-plane and a length or a vector describing the direction and a length, add geogrid features to them and directly set their properties.

# Creates multiple objects, the last one is the Geogrid object ([-1])
material_i = g_i.geogridmat()
geogrid_g = g_i.geogrid((1, 2), "relative", (3, 4), "Material", material_i)[-1]
print(geogrid_g)
```

---

## INPUT: geogridmat

# Python wrapper commands [GEOGRIDMAT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## geogridmat 
Creates a geogrid material set.

```python
s_i.new()
```

```python
# Alternative 1
g_i.geogridmat()
```

---

## INPUT: getcurveresults

# Python wrapper commands [GETCURVERESULTS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## getcurveresults 
Displays the calculated values of a particular block in the curves data file of the specified phase.

```python
s_i.new()

# Import new_server function from plxscripting module to connect to PLAXIS 2D Output application
from plxscripting.easy import *
```

```python
# Alternative 1
# Displays the values of the calculation results of a specified block in a phase. The values shown are the values in the last step of the calculation.

# Creates a borehole, adds soillayer and defines material properties
borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[0].Material = material

# Changes the mode, adds a lineload and generates the mesh
g_i.gotostructures()
g_i.lineload((3, 0), (7, 0))

g_i.gotomesh()
g_i.mesh(0.075)

# Connect to the PLAXIS 2D Output application with the correct port for the remote scripting server
output_port = g_i.selectmeshpoints()
s_o, g_o = new_server("localhost", port=output_port, password=s_i.connection._password)

# Adds a curvepoints, changes the mode, defines phases
g_o.addcurvepoint("Node", (5, -2))
g_o.update()

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
g_i.LineLoads[-1].Active[phase1_s] = True
g_i.calculate()

g_i.getcurveresults(phase1_s, "WPNDIN_R")
```

```python
# Alternative 2
# Displays a specific calculation result of a specified block in a phase.

print(g_i.getcurveresults(phase1_s, "DISPLACR", 1))
```

```python
# Alternative 3
# Displays the values of the calculation results of column of a specified block in a phase.

print(g_i.getcurveresults(phase1_s, "MULTIPLR", 0, 3))
```

---

## INPUT: getnormal

# Python wrapper commands [GETNORMAL]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## getnormal
Displays the normal of a polycurve.

```python
s_i.new()
```

```python
# Alternative 1
# Creates multiple objects, the first one is the Polycurve object ([0])
polycurve_g = g_i.polycurve((0, 0), "line", 0, 2, "arc", 45, 90, 3)[0]
print(polycurve_g.getnormal())
```

---

## INPUT: getresults

# Python wrapper commands [GETRESULTS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## getresults
Displays calculation results.

```python
s_i.new()
```

```python
# Alternative 1
# Displays the minimum and maximum value of the calculation results of a specified block in a phase.

# Creates a borehole, adds soillayer and defines material properties
borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[-1].Material = material

# Changes the mode, adds a lineload and generates the mesh
g_i.gotostructures()
g_i.lineload((3, 0), (7, 0), "qy_start", 50)

g_i.gotomesh()
g_i.mesh(0.075)

# Changes the mode, defines phases and activates the lineload
g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
g_i.LineLoads[-1].Active[phase1_s] = True
g_i.calculate()

g_i.getresults(phase1_s, "UTOT___R")
```

```python
# Alternative 2
# Displays a specific calculation result of a specified block in a phase.

print(g_i.getresults(phase1_s, "UTOT___R", 13))
```

```python
# Alternative 3
# Displays the minimum and maximum or uniform value of the calculation results of column of a specified block in a phase.

print(g_i.getresults(phase1_s, "UTOT___R", "rows", 2, 6))
```

```python
# Alternative 4
# Displays all of the calculation results of column of a specified block in a phase.

print(g_i.getresults(phase1_s, "UTOT___R", "columns", 12, 2))
```

---

## INPUT: getsoillayerlevel

# Python wrapper commands [GETSOILLAYERLEVEL]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## getsoillayerlevel
Returns the location of a soil layer boundary at a borehole.

```python
s_i.new()
```

```python
# Alternative 1
borehole_g = g_i.borehole(0)
g_i.soillayer(10)

g_i.getsoillayerlevel(borehole_g, 1)
```

---

## INPUT: getsoillayerporepressure

# Python wrapper commands [GETSOILLAYERPOREPRESSURE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## getsoillayerporepressure
Returns the pore pressures of a soil layer.

```python
s_i.new()
```

```python
# Alternative 1
borehole_g = g_i.borehole(0)
borehole_g.Head = 2
g_i.soillayer(10)
soillayer_g = g_i.SoilLayers[-1]

g_i.getsoillayerporepressure(borehole_g, soillayer_g)
```

---

## INPUT: gettoggle

# Python wrapper commands [GETTOGGLE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## gettoggle
Returns true or false depending on whether the toggle is set to true or false. If a toggle is absent, it returns false.

```python
s_i.new()
```

```python
# Alternative 1
g_i.gettoggle("NO_CONTROLLERS")
```

---

## INPUT: gotoflow

# Python wrapper commands [GOTOFLOW]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## gotoflow 
Switches to flow conditions mode.

```python
s_i.new()
```

```python
# Alternative 1
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))

g_i.gotoflow()
```

```python
# Alternative 2
g_i.gotosoil()
g_i.gotoflow(True)
```

---

## INPUT: gotomesh

# Python wrapper commands [GOTOMESH]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## gotomesh
Switches to Mesh mode.

```python
s_i.new()
```

```python
# Alternative 1
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))

g_i.gotomesh()
```

```python
# Alternative 2
g_i.gotosoil()
g_i.gotomesh(True)
```

---

## INPUT: gotosoil

# Python wrapper commands [GOTOSOIL]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## gotosoil
Switches to Soil mode.

```python
s_i.new()
```

```python
# Alternative 1
g_i.gotosoil()
```

---

## INPUT: gotostages

# Python wrapper commands [GOTOSTAGES]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## gotostages
Switches to Staged construction mode.

```python
s_i.new()
```

```python
# Alternative 1
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))

g_i.gotostages()
```

```python
# Alternative 2
g_i.gotosoil()
g_i.gotostages(True)
```

---

## INPUT: gotostructures

# Python wrapper commands [GOTOSTRUCTURES]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## gotostructures
Switches to Structures mode.

```python
s_i.new()
```

```python
# Alternative 1
g_i.gotostructures()
```

---

## INPUT: gotowater

# Python wrapper commands [GOTOWATER]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## gotowater
Switches to flow conditions mode.

```python
s_i.new()
```

```python
# Alternative 1
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))
g_i.gotowater()
```

```python
# Alternative 2
g_i.gotosoil()
g_i.gotowater(True)
```

---

## INPUT: group

# Python wrapper commands [GROUP]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## group
Makes a group of one or more objects.

```python
s_i.new()
```

```python
# Alternative 1
# Groups one or more objects.

# Creates multiple objects, the first one is the Polygon object ([0])
point1_g, point2_g = g_i.point((1, 1), (2, 2))
polygon_g = g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))[0]

group_g = g_i.group(polygon_g, point1_g, point2_g)
print(group_g)
```

```python
# Alternative 2
# Groups specified features of one or more objects.

res = g_i.line((0, 0), (1, 2), (2, 3), (4, 5), (6, 7))
lines_g = [item for item in res if item._plx_type == 'Line']
g_i.plate(lines_g)

group_g = g_i.group(lines_g[-3], lines_g[-2], lines_g[-1], "plate")
print(group_g)
```

---

## INPUT: groupfiltered

# Python wrapper commands [GROUPFILTERED]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## groupfiltered
Makes a group of one or more objects that fulfill a certain criterion.

```python
s_i.new()
```

```python
# Alternative 1
# Example 1
g_i.point((3, 4), (2, 2), (2, 3))
points_g = g_i.Points

group_g = g_i.groupfiltered(points_g, "x=2")
print(group_g, group_g[:])

# Example 2
# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((3, 2), (5, 6))[-1]
line2_g = g_i.line((4, 2), "relative", (3, 4))[-1]
g_i.lineload((line1_g, line2_g), "qx_start", 3, "qy_start", 7)
g_i.lineload((1, 2), "relative", (3, 4), "qx_start", 3, "qy_start", 3)

lineloads_i = g_i.LineLoads

group_g = g_i.groupfiltered(lineloads_i, "qy_start>5")
print(group_g, group_g[:])
```

---

## INPUT: gwfbc

# Python wrapper commands [GWFBC]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## gwfbc
Adds groundwater flow boundary condition features to lines.

```python
s_i.new()
```

```python
# Alternative 1
# Adds groundwater flow boundary condition features to one or more existing lines in the geometry.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((0, 0), (1, 1))[-1]
gwflowbc_g = g_i.gwfbc(line_g)
print(gwflowbc_g)

# Example 2
line1_g = g_i.line((0, 2), (2, 2))[-1]
line2_g = g_i.line((2, 2), (2, 0))[-1]
gwflowbcs_g = g_i.gwfbc(line1_g, line2_g)
print(gwflowbcs_g)
```

```python
# Alternative 2
# Creates a line between two points (which may either exist, or will be created) and add a groundwater flow boundary condition feature to it.

# Example 1
# Creates multiple objects, the last one is the GWFlowBC object ([-1])
point_g = g_i.point(0, 0)
gwflowbc_g = g_i.gwfbc(point_g, (5, 6))[-1]
print(gwflowbc_g)

# Example 2
points_g = g_i.point((1, 1), (1, 4))
line_g, gwflowbc_g = g_i.gwfbc(points_g[-2], points_g[-1])
print(gwflowbc_g)

# Example 3
gwflowbc_g = g_i.gwfbc((5, 5), (5, 2))[-1]
print(gwflowbc_g)
```

```python
# Alternative 3
# Creates lines between three or more points (which may either exist, or will be created) and add groundwater flow boundary condition features to them.

points_g = g_i.point((1, 1), (4, 4))
res = g_i.gwfbc(points_g[-2], (2, 3), points_g[-1])
gwflowbcs_g = [item for item in res if item._plx_type == 'GWFlowBC']
print(gwflowbcs_g)
```

```python
s_i.new()
```

```python
# Alternative 4
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect
# to the xy-plane and a length or a vector describing the direction and a length and add groundwater flow boundary condition features to them.

# Example 1
# Creates multiple objects, the last one is the GWFlowBC object ([-1])
gwflowbc_g = g_i.gwfbc((1, 2), "relative", (3, 4))[-1]
print(gwflowbc_g)

# Example 2
point_g = (1, 2)
res = g_i.gwfbc(point_g, "relative", (3, 4), (-5, -9), "angles", 30, 16)
gwflowbcs_g = [item for item in res if item._plx_type == 'GWFlowBC']
print(gwflowbcs_g)

# Example 3
res = g_i.gwfbc((1, 2), "angles", 45, 10, "absolute", (4, 5))
gwflowbcs_g = [item for item in res if item._plx_type == 'GWFlowBC']
print(gwflowbcs_g)
```

```python
# Alternative 5
# Adds groundwater flow boundary condition features to one or more existing lines in the geometry and directly set their properties.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((2, 2), (3, 3))[-1]
gwflowbc_g = g_i.gwfbc(line_g, "Behaviour", "Closed")
print(gwflowbc_g)

# Example 2
line1_g = g_i.line((2, 4), (3, 4))[-1]
line2_g = g_i.line((0, 2), (1, 2))[-1]
gwflowbcs_g = g_i.gwfbc(line1_g, line2_g, "Behaviour", "Closed")
print(gwflowbcs_g)
```

```python
# Alternative 6
# Creates a line between two points (which may either exist, or will be created), add a groundwater flow boundary condition feature 
# to it and directly set its properties.

# Creates multiple objects, the last one is the GWFlowBC object ([-1])
point_g = g_i.point(1, 1)
gwflowbc_g = g_i.gwfbc(point_g, (5, 6), "Behaviour", "Closed")[-1]
print(gwflowbc_g)
```

```python
# Alternative 7
# Creates lines between three or more points (which may either exist, or will be created), add groundwater flow boundary condition features 
# to them and directly set their properties.

point1_g, point2_g = g_i.point((1, 1), (8, 9))
res = g_i.gwfbc(point1_g, (5.1, 6.4), point2_g, "Behaviour", "Closed")
gwflowbcs_g = [item for item in res if item._plx_type == 'GWFlowBC']
print(gwflowbcs_g)
```

```python
# Alternative 8
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect 
# to the xy-plane and a length or a vector describing the direction and a length, add groundwater flow boundary condition features 
# to them and directly set their properties.

# Creates multiple objects, the last one is the GWFlowBC object ([-1])
gwflowbc_g = g_i.gwfbc((1, 2), "relative", (3, 4), "Behaviour", "Closed")[-1]
print(gwflowbc_g)

# Obtain Behaviour property value assigned for all Groundwater flow boundaray conditions in a list and display them
gwflowbcs_behaviour= g_i.GroundwaterFlowBCs.Behaviour.value
print(f'Groundwaterflow BCs Behaviour property: {gwflowbcs_behaviour}')
```

---

## INPUT: headfunction

# Python wrapper commands [HEADFUNCTION]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## headfunction 
Adds a head function.

```python
s_i.new()
```

```python
# Alternative 1
for i in range(3):
    g_i.headfunction()

print(g_i.tabulate(g_i.FlowFunctions))

# Obtain Signal property value assigned for all head functions in a list and display them
headfunctions_signal = g_i.FlowFunctions.Signal.value
print(f'Head functions signal: {headfunctions_signal}')
```

---

## INPUT: heatfluxfunction

# Python wrapper commands [HEATFLUXFUNCTION]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## heatfluxfunction 
Adds a heat flux function.

```python
s_i.new()
```

```python
# Alternative 1
for i in range(3):
    g_i.heatfluxfunction()

print(g_i.tabulate(g_i.ThermalFunctions))

# Obtain Signal property value assigned for all head functions in a list and display them
heatfluxfunctions_signal = g_i.ThermalFunctions.Signal.value
print(f'Heat flux functions signal: {heatfluxfunctions_signal}')
```

---

## INPUT: heattotalfluxfunction

# Python wrapper commands [HEATTOTALFLUXFUNCTION]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## heattotalfluxfunction 
Adds a heat total flux function.

```python
s_i.new()
```

```python
# Alternative 1
for i in range(3):
    g_i.heattotalfluxfunction()

print(g_i.tabulate(g_i.ThermalFunctions))

# Obtain Signal property value assigned for all head functions in a list and display them
heattotalfluxfunctions_signal = g_i.ThermalFunctions.Signal.value
print(f'Heat total flux functions signal: {heattotalfluxfunctions_signal}')
```

---

## INPUT: help

# Python wrapper commands [HELP]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## help
Displays a short help for the command line functionality.

```python
s_i.new()
```

```python
# Alternative 1
print(g_i.help())
```

---

## INPUT: import

# Python wrapper commands [IMPORT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## import
Imports points, polycurves, surfaces, structural or soil volumes.

```python
s_i.new()
```

```python
# Alternative 1
# Example 1
print(g_i.import_("points", "C:\PLAXIS2D\geometry_file_dxf.dxf", (1, 1), (0, 0)))

# Example 2
print(g_i.import_("lines", "C:\PLAXIS2D\geometry_file_dxf.dxf", (1, 1), (0, 0)))

# Example 3
print(g_i.import_("points|lines|polygons", "C:\PLAXIS2D\geometry_file_dxf.dxf", (2, 2), (1, 1)))
```

---

## INPUT: importcrosssection

# Python wrapper commands [IMPORTCROSSSECTION]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## importcrosssection
Import one or more polycurves into the cross-section of a tunnel. If the cross-section of the tunnel is not empty the imported segments are added to the end of the segment list. If the file contains more than one polycurves, the one with the largest bounding box will be imported as the cross-section and the others as sub-sections. The imported polycurves can only contain line and arc segments and they should be positioned on the XY-plane.

```python
s_i.new()
```

```python
# Alternative 1
tunnel_g = g_i.tunnel(0, 0)
g_i.importcrosssection(tunnel_g, "C:\PLAXIS2D\polylineXY.dxf")
```

---

## INPUT: importfielddata

# Python wrapper commands [IMPORTFIELDDATA]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## importfielddata
Imports field data.

```python
s_i.new()
```

```python
# Alternative 1
fielddata_g = g_i.importfielddata(r"C:\PLAXIS2D\test1.cpt")

print(fielddata_g)
```

---

## INPUT: info

# Python wrapper commands [INFO]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## info
Displays all commands and attributes for an object.

```python
s_i.new()
```

```python
# Alternative 1
print(g_i.info(g_i.Materials))
```

```python
# Alternative 2
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((0, 2), (-5, 2))[-1]
print(line_g.info())
```

```python
# Alternative 3
# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((0, 2), (-5, 2))[-1]
line2_g = g_i.line((1, 2), "relative", (3, 4))[-1]
print(g_i.info(line1_g, line2_g))
```

---

## INPUT: initializerectangular

# Python wrapper commands [INITIALIZERECTANGULAR]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## initializerectangular
Changes the coordinates of the rectangular soil contour.

```python
s_i.new()
```

```python
# Alternative 1
g_i.SoilContour.initializerectangular(1, 5, 18, 7)
```

---

## INPUT: insert

# Python wrapper commands [INSERT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## insert
Inserts a section into a polycurve or an advanced table row.

```python
s_i.new()
```

```python
# Alternative 1
# Inserts a line section with a length of 1 into a polycurve.

# Creates multiple objects, the first one is the Polycurve object ([0])
polycurve_g = g_i.polycurve((0, 0), "line", 0, 2, "arc", 45, 90, 3)[0]
segment_g = polycurve_g.insert(2)
print(segment_g)
```

```python
# Alternative 2
# Inserts a section with specified properties into a polycurve.

# Example 1
# Creates multiple objects, the first one is the Polycurve object ([0])
polycurve_g = g_i.polycurve((3, 0), "line", 0, 2, "arc", 45, 90, 3)[0]
segment_g = polycurve_g.insert(2, "arc", 90, 45, 2)
print(segment_g)

# Example 2
polycurve_g = g_i.polycurve((6, 0), "line", 0, 2, "arc", 45, 90, 3)[0]

segment_g = polycurve_g.insert(0, "line", 0, 5)
print(segment_g)
```

```python
# Alternative 3
# Inserts a row into an advanced table.

loadmultiplier_g = g_i.loadmultiplier()
loadmultiplier_g.Table.insert(0)
```

---

## INPUT: insertphase

# Python wrapper commands [INSERTPHASE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## insertphase
Creates a new phase and inserts it before an existing phase.

```python
s_i.new()
```

```python
# Alternative 1
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))

g_i.gotostages()
phase0_s = g_i.Phases[0]
phase1_s = g_i.phase(phase0_s)

phase2_s = g_i.insertphase(phase1_s)
print(phase2_s)
```

---

## INPUT: insertpoint

# Python wrapper commands [INSERTPOINT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## insertpoint
Inserts a new point to an existing polygon or water level.

```python
s_i.new()
```

```python
# Alternative 1
# Inserts a new point to an existing polygon before a specified point of the polygon.

# Creates multiple objects, the first one is the Polygon object ([0])
polygon_g = g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))[0]

polygon_g.insertpoint(5, (1, 2))
```

```python
# Alternative 2
# Inserts a new point to an existing water level before a specified point of the water level without specifying the pinc.

g_i.gotoflow()
waterlevel_s = g_i.waterlevel((0, 2), (2, 3), (3, 3))

waterlevel_s.insertpoint(2, (3, 4))
```

---

## INPUT: insertsoillayer

# Python wrapper commands [INSERTSOILLAYER]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## insertsoillayer 
Creates a new soil layer above an existing soil layer.

```python
s_i.new()
```

```python
# Alternative 1 
borehole_g = g_i.borehole(0)
g_i.soillayer(5)
g_i.soillayer(10)
soillayer_g = g_i.SoilLayers[-1]

g_i.insertsoillayer(soillayer_g)
```

---

## INPUT: insertsubcurve

# Python wrapper commands [INSERTSUBCURVE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## insertsubcurve
Inserts a sub section to a tunnel cross section.

```python
s_i.new()
```

```python
# Alternative 1
# Inserts a sub section into a tunnel cross section.

tunnel_g = g_i.tunnel(0, 0)
tunnel_g.CrossSection.insertsubcurve(0)
```

```python
# Alternative 2
# Inserts one or more sub sections with specified properties to a tunnel cross section.

tunnel_g = g_i.tunnel(2, 2)
tunnel_g.CrossSection.addsubcurve()
tunnel_g.CrossSection.addsubcurve()
tunnel_g.CrossSection.insertsubcurve(1, "line", 5.0, 3.0, 45.0, 2.0, "arc", 1.0, 3.0, 30.0, 45.0, 1)
```

---

## INPUT: insertwaterpoint

# Python wrapper commands [INSERTWATERPOINT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## insertwaterpoint
Inserts a new point to an existing water level.

```python
s_i.new()
```

```python
# Alternative 1
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))

g_i.gotoflow()
waterlevel_s = g_i.waterlevel((0, 2), (2, 3), (3, 3))
waterlevel_s.insertwaterpoint(1, (2, 6), -5)
```

---

## INPUT: intersectsegments

# Python wrapper commands [INTERSECTSEGMENTS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## intersectsegments
Insertsects sub sections of a tunnel cross section.

```python
s_i.new()
```

```python
# Alternative 1
tunnel_g = g_i.tunnel(0, 0)
segments_g = tunnel_g.CrossSection.add("line", 0, 2, "line", 90, 1, "line", 0, 3)
subsection_g = tunnel_g.CrossSection.addsubcurve("line", 2, 3, 45, 1)[0]

tunnel_g.CrossSection.intersectsegments(segments_g[-1], subsection_g)
```

---

## INPUT: invertdirection

# Python wrapper commands [INVERTDIRECTION]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## invertdirection
Inverts the direction of a line.

```python
s_i.new()
```

```python
# Alternative 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((0, 2), (-5, 2))[-1]
g_i.invertdirection(line_g)
```

---

## INPUT: kill

# Python wrapper commands [KILL]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## kill
Closes down PLAXIS Input without saving.

```python
s_i.new()
```

```python
# Alternative 1
# g_i.kill()
```

---

## INPUT: line

# Python wrapper commands [LINE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## line
Creates a line.

```python
s_i.new()
```

```python
# Alternative 1
# Creates a line between two points.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((5, 6), (8, 9))[-1]
print(line_g)

# Example 2
point_g = g_i.point(2, 3)
line_g = g_i.line((1, 2), point_g)[-1]
print(line_g)

# Example 3
point_g = g_i.point(5, 6)
line_g = g_i.line(point_g, (8, 4))[-1]
print(line_g)

# Example 4
point1_g, point2_g = g_i.point((3, 4), (1, 1))
line_g = g_i.line(point1_g, point2_g)
print(line_g)
```

```python
# Alternative 2
# Creates a line between two or more points.

# Example 1
point1_g, point2_g, point3_g = g_i.point((3, 4), (1, 1), (5, 6))
res = g_i.line(point1_g, point2_g, point3_g)
lines_g = [item for item in res if item._plx_type == 'Line']
print(lines_g)

# Example 2
point1_g, point2_g = g_i.point((3, 9), (4, 1))
res = g_i.line(point1_g, (1, 2), point2_g)
lines_g = [item for item in res if item._plx_type == 'Line']
print(lines_g)

# Example 3
point_g = g_i.point(3, 6)
res = g_i.line((1, 0), (9, 4), (8, 6), point_g)
lines_g = [item for item in res if item._plx_type == 'Line']
print(lines_g)
```

```python
# Alternative 3
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angle with respect 
# to the xy-plane and a length or a vector describing the direction and a length.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((1, 2), "relative", (3, 4))[-1]
print(line_g)

# Example 2
point_g = g_i.point(2, 2)

res = g_i.line(point_g, "relative", (3, 4), (-5, -9), "angles", 30, 16)
lines_g = [item for item in res if item._plx_type == 'Line']
print(lines_g)

# Example 3
res = g_i.line((2, 3), "angles", 45, 10, "absolute", (4, 5))
lines_g = [item for item in res if item._plx_type == 'Line']
print(lines_g)

# Example 4
res = g_i.line((1, 3), "angles", 45, 10, "vector", (8, 2), 14)
lines_g = [item for item in res if item._plx_type == 'Line']
print(lines_g)

# Obtain Length property value for all lines in a list and display them
lines_length = g_i.Lines.Length.value
print(f'Lines length: {lines_length}')
```

---

## INPUT: lineangles

# Python wrapper commands [LINEANGLES]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## lineangles
Creates lines in directions specified using an angle.

```python
s_i.new()
```

```python
# Alternative 1
# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
point_g = g_i.point(2, 2)
line_g = g_i.lineangles(point_g, 30, 16)[-1]
print(line_g)

# Example 2
line_g = g_i.lineangles((1, 2), 45, 9)[-1]
print(line_g)

# Example 3
point_g = g_i.point(5, 0)
line1_g = g_i.line((5, 5), (8, 5))[-1]
line2_g = g_i.lineangles(point_g, 90, line1_g)[-1]
print(line2_g)
```

---

## INPUT: linedispl

# Python wrapper commands [LINEDISPL]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## linedispl
Adds line prescribed displacement features to lines.

```python
s_i.new()
```

```python
# Alternative 1
# Adds line prescribed displacement features to one or more existing lines in the geometry.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((5, 6), (8, 9))[-1]
linedisplacement_g = g_i.linedispl(line_g)
print(linedisplacement_g)

# Example 2
line1_g = g_i.line((0, 2), (-5, 2))[-1]
line2_g = g_i.line((1, 2), "relative", (3, 4))[-1]

linedisplacements_g = g_i.linedispl(line1_g, line2_g)
print(linedisplacements_g)

# Example 3
line1_g = g_i.line((6, 8), (5, 9))[-1]
line2_g = g_i.line((2, 3), "relative", (3, 4))[-1]

linedisplacements_g = g_i.linedispl((line1_g, line2_g))
print(linedisplacements_g)

# Example 4
line1_g = g_i.line((5, 9), (8, 8))[-1]
line2_g = g_i.line((1, 2), "relative", (5, 4))[-1]
group_g = g_i.group(line1_g, line2_g)

linedisplacements_g = g_i.linedispl(group_g)
print(linedisplacements_g)
```

```python
# Alternative 2
# Creates a line between two points (which may either exist, or will be created) and add a line prescribed displacement feature to it.

# Example 1
# Creates multiple objects, last two are Line and LineDisplacement objects respectively
point_g = g_i.point(3, 4)
line_g, linedisplacement_g = g_i.linedispl(point_g, (5, 6))[-2:]
print(line_g, linedisplacement_g)

# Example 2
point1_g, point2_g = g_i.point((5, 2), (7, 3))
line_g, linedisplacement_g = g_i.linedispl(point1_g, point2_g)
print(line_g, linedisplacement_g)

# Example 3
line_g, linedisplacement_g = g_i.linedispl((1, 4), (6, 5))[-2:]
print(line_g, linedisplacement_g)
```

```python
# Alternative 3
# Creates lines between three or more points (which may either exist, or will be created) and add line prescribed displacement features to them.

point1_g, point2_g = g_i.point((3, 9), (5, 10))

res = g_i.linedispl(point1_g, (5.1, 7.2), point2_g)
lines_g = [item for item in res if item._plx_type == 'Line']
linedisplacements_g = [item for item in res if item._plx_type == 'LineDisplacement']
print(lines_g, linedisplacements_g)
```

```python
# Alternative 4
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect 
# to the xy-plane and a length or a vector describing the direction and a length and add line prescribed displacement features to them.

# Example 1
# Creates multiple objects, last two are Line and LineDisplacement objects respectively
line_g, linedisplacement_g = g_i.linedispl((1, 2), "relative", (3, 4))[-2:]
print(line_g, linedisplacement_g)

# Example 2
point_g = g_i.point(3, 9)
res = g_i.linedispl(point_g, "relative", (3, 4), (-5, -9), "angles", 30, 16)
lines_g = [item for item in res if item._plx_type == 'Line']
linedisplacements_g = [item for item in res if item._plx_type == 'LineDisplacement']
print(lines_g, linedisplacements_g)

# Example 3
res = g_i.linedispl((1, 3), "angles", 45, 10, "absolute", (4, 5))
lines_g = [item for item in res if item._plx_type == 'Line']
linedisplacements_g = [item for item in res if item._plx_type == 'LineDisplacement']
print(lines_g, linedisplacements_g)
```

```python
# Alternative 5
# Adds line prescribed displacement features to one or more existing lines in the geometry and directly set their properties.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((8, 9), (8, 10))[-1]
linedisplacement_g = g_i.linedispl(line_g, "Displacement_x", "Fixed",
                                   "Displacement_y", "Prescribed")
print(linedisplacement_g)

# Example 2
line1_g = g_i.line((3, 7), (5, 6))[-1]
line2_g = g_i.line((4, 2), "relative", (3, 4))[-1]
linedisplacements_g = g_i.linedispl((line1_g, line2_g), "Displacement_x", 
                                    "Fixed", "Displacement_y", "Prescribed")
print(linedisplacements_g)
```

```python
# Alternative 6
# Creates a line between two points (which may either exist, or will be created), add a line prescribed displacement feature to it and directly set its properties.

# Creates multiple objects, last two are Line and LineDisplacement objects respectively
point_g = g_i.point(3, 4)
line_g, linedisplacement_g = g_i.linedispl(point_g, (5, 6), "Displacement_x", "Fixed", 
                                           "Displacement_y", "Prescribed")[-2:]
print(line_g, linedisplacement_g)
```

```python
# Alternative 7
point1_g, point2_g = g_i.point((5, 7), (4, 10))

res = g_i.linedispl(point1_g, (5.1, 6.4), point2_g, "Displacement_x", "Fixed",
                    "Displacement_y", "Prescribed")
lines_g = [item for item in res if item._plx_type == 'Line']
linedisplacements_g = [item for item in res if item._plx_type == 'LineDisplacement']
print(lines_g, linedisplacements_g)
```

```python
# Alternative 8
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect 
# to the xy-plane and a length or a vector describing the direction and a length, add line prescribed displacement features to them and directly set their properties.

# Creates multiple objects, last two are Line and LineDisplacement objects respectively
line_g, linedisplacement_g = g_i.linedispl((1, 2), "relative", (3, 8), 
                                           "Displacement_x", "Fixed", 
                                           "Displacement_y", "Prescribed")[-2:]
print(line_g, linedisplacement_g)


# Obtain Displacement_y property value assigned for all line displacements in a list and display them
linedispls_disp_y = g_i.LineDisplacements.Displacement_y.value
print(f'Line displacments Displacement_y property: {linedispls_disp_y}')
```

---

## INPUT: lineload

# Python wrapper commands [LINELOAD]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## lineload
Adds line load features to lines.

```python
s_i.new()
```

```python
# Alternative 1
# Adds line load features to one or more existing lines in the geometry.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((5, 6), (8, 9))[-1]
lineload_g = g_i.lineload(line_g)
print(lineload_g)

# Example 2
line1_g = g_i.line((0, 2), (-5, 2))[-1]
line2_g = g_i.line((1, 2), "relative", (3, 4))[-1]

lineloads_g = g_i.lineload(line1_g, line2_g)
print(lineloads_g)

# Example 3
line1_g = g_i.line((6, 8), (5, 9))[-1]
line2_g = g_i.line((2, 3), "relative", (3, 4))[-1]

lineloads_g = g_i.lineload((line1_g, line2_g))
print(lineloads_g)

# Example 4
line1_g = g_i.line((5, 9), (8, 8))[-1]
line2_g = g_i.line((1, 2), "relative", (5, 4))[-1]
group_g = g_i.group(line1_g, line2_g)

lineloads_g = g_i.lineload(group_g)
print(lineloads_g)
```

```python
# Alternative 2
# Creates a line between two points (which may either exist, or will be created) and add a line load feature to it.

# Example 1
# Creates multiple objects, last two are Line and LineLoad objects respectively
point_g = g_i.point(3, 4)
line_g, lineload_g = g_i.lineload(point_g, (5, 6))[-2:] 
print(line_g, lineload_g)

# Example 2
point1_g, point2_g = g_i.point((5, 2), (7, 3))
line_g, lineload_g = g_i.lineload(point1_g, point2_g) 
print(line_g, lineload_g)

# Example 3
line_g, lineload_g = g_i.lineload((1, 4), (6, 5))[-2:] 
print(line_g, lineload_g)
```

```python
# Alternative 3
# Creates lines between three or more points (which may either exist, or will be created) and add line load features to them.

point1_g, point2_g = g_i.point((3, 9), (5, 10))

res = g_i.lineload(point1_g, (5.1, 7.2), point2_g)
lines_g = [item for item in res if item._plx_type == 'Line']
lineloads_g = [item for item in res if item._plx_type == 'LineLoad']
print(lines_g, lineloads_g)
```

```python
# Alternative 4
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect 
# to the xy-plane and a length or a vector describing the direction and a length and add line load features to them.

# Example 1
# Creates multiple objects, last two are Line and LineLoad objects respectively
line_g, lineload_g = g_i.lineload((1, 2), "relative", (3, 4))[-2:]
print(line_g, lineload_g)

# Example 2
point_g = g_i.point(3, 9)
res = g_i.lineload(point_g, "relative", (3, 4), (-5, -9), "angles", 30, 16)
lines_g = [item for item in res if item._plx_type == 'Line']
lineloads_g = [item for item in res if item._plx_type == 'LineLoad']
print(lines_g, lineloads_g)

# Example 3
res = g_i.lineload((1, 3), "angles", 45, 10, "absolute", (4, 5))
lines_g = [item for item in res if item._plx_type == 'Line']
lineloads_g = [item for item in res if item._plx_type == 'LineLoad']
print(lines_g, lineloads_g)
```

```python
# Alternative 5
# Adds line load features to one or more existing lines in the geometry and directly set their properties.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((8, 9), (8, 10))[-1] 
lineload_g = g_i.lineload(line_g, "qx_start", 3, "qy_start", 7)
print(lineload_g)

# Example 2
line1_g = g_i.line((3, 7), (5, 6))[-1] 
line2_g = g_i.line((4, 2), "relative", (3, 4))[-1] 
lineloads_g = g_i.lineload((line1_g, line2_g), "qx_start", 3, "qy_start", 7)
print(lineloads_g)
```

```python
# Alternative 6
# Creates a line between two points (which may either exist, or will be created), add a line load feature to it and directly set its properties.

# Creates multiple objects, last two are Line and LineLoad objects respectively
point_g = g_i.point(3, 4)
line_g, lineload_g = g_i.lineload(point_g, (5, 6), "qx_start", 3, "qy_start", 7)[-2:]
print(line_g, lineload_g)
```

```python
# Alternative 7
# Creates lines between three or more points (which may either exist, or will be created), add line load features to them and directly set their properties.

point1_g, point2_g = g_i.point((5, 7), (4, 10))

res = g_i.lineload(point1_g, (5.1, 6.4), point2_g, "qx_start", 3, "qy_start", 7)
lines_g = [item for item in res if item._plx_type == 'Line']
lineloads_g = [item for item in res if item._plx_type == 'LineLoad']
print(lines_g, lineloads_g)
```

```python
# Alternative 8
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect
# to the xy-plane and a length or a vector describing the direction and a length, add line load features to them and directly set their properties.

# Creates multiple objects, last two are Line and LineLoad objects respectively
line_g, lineload_g = g_i.lineload((1, 2), "relative", (3, 8), 
                                  "qx_start", 3, "qy_start", 7)[-2:]
print(line_g, lineload_g)

# Obtain Distribution property value assigned for all line loads in a list and display them
lineloads_distribution = g_i.LineLoads.Distribution.value
print(f'Line Loads Distribution property: {lineloads_distribution}')
```

---

## INPUT: lineparallel

# Python wrapper commands [LINEPARALLEL]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## lineparallel
Creates a line parallel to another line.

```python
s_i.new()
```

```python
# Alternative 1
# Creates a line from a point (which may either exist, or will be created) parallel to an existing line with the same length.

# Creates multiple objects, the last one is the Line object ([-1])
point_g = g_i.point(2, 2)
line1_g = g_i.line((5, 6), (8, 9))[-1] 
line_g = g_i.lineparallel(point_g, line1_g)[-1]
print(line_g)
```

```python
# Alternative 2
# Creates a line from a point (which may either exist, or will be created) parallel to an existing line with a specified length.

# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((6, 7), (9, 10))[-1]
line_g = g_i.lineparallel((0, 1), line1_g, 10)[-1]
print(line_g)
```

---

## INPUT: linerelative

# Python wrapper commands [LINERELATIVE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## linerelative
Creates lines using relative coordinates.

```python
s_i.new()
```

```python
# Alternative 1
# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
point_g = g_i.point(2, 4)
line_g = g_i.linerelative(point_g, (6, 8))[-1]
print(line_g)

# Example 2
point_g = g_i.point(2, 3)
res = g_i.linerelative(point_g, (6, 4), (1, 3))
lines_g = [item for item in res if item._plx_type == 'Line']
print(lines_g)
```

---

## INPUT: linevector

# Python wrapper commands [LINEVECTOR]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## linevector
Creates lines in directions specified using vectors.

```python
s_i.new()
```

```python
# Alternative 1
# Creates multiple objects, the last one is the Line object ([-1])

# Example 1
point_g = g_i.point(2, 4)
line_g = g_i.linevector(point_g, (6, 8), 14)[-1]
print(line_g)

# Example 2
res = g_i.linevector((1, 2), (5, 4), 12, (9, 8), 10)
lines_g = [item for item in res if item._plx_type == 'Line']
print(lines_g)

# Example 3
point_g = g_i.point(0, 0)
line1_g = g_i.line((0, 3.2), (-5, 3.2))[-1]
line_g = g_i.linevector(point_g, (-1, 3.2), line1_g)[-1]
print(line_g)
```

---

## INPUT: loadfactorlabel

# Python wrapper commands [LOADFACTORLABEL]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## loadfactorlabel 
Adds a load factor label for design approaches.

```python
s_i.new()
```

```python
# Alternative 1
loadfactorlabel_g = g_i.loadfactorlabel()
print(loadfactorlabel_g)
```

---

## INPUT: loadmultiplier

# Python wrapper commands [LOADMULTIPLIER]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## loadmultiplier
Adds a load multiplier.

```python
s_i.new()
```

```python
# Alternative 1
for i in range(3):
    g_i.loadmultiplier()

print(g_i.tabulate(g_i.DynamicMultipliers))

# Obtain Signal property value assigned for all head functions in a list and display them
loadmultipliers_signal = g_i.DynamicMultipliers.Signal.value
print(f'Load multipliers signal: {loadmultipliers_signal}')
```

---

## INPUT: materialcommand

# Python wrapper commands [MATERIALFACTORLABEL]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## materialfactorlabel
Adds a material factor label for design approaches.

```python
s_i.new()
```

```python
# Alternative 1
materialfactorlabel_g = g_i.materialfactorlabel()
print(materialfactorlabel_g)
```

---

## INPUT: materialfactorlabel

# Python wrapper commands [MATERIALFACTORLABEL]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## materialfactorlabel
Adds a material factor label for design approaches.

```python
s_i.new()
```

```python
# Alternative 1
materialfactorlabel_g = g_i.materialfactorlabel()
print(materialfactorlabel_g)
```

---

## INPUT: mergeequivalents

# Python wrapper commands [MERGEEQUIVALENTS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## mergeequivalents
Merges geometric objects with a default tolerance value of 0.001 or with an optional tolerance parameter. This command removes existing objects and creates new features. The specified objects are used as initial merge set. It is possible that the merge operation will also affect objects that are directly or indirectly connected to the initial merge set (e.g. the lines connected to explicitly specified points will implicitly be taken into account during the merge operation).

```python
s_i.new()
```

```python
# Alternative 1
# Merges objects with a default tolerance value of 0.001. This command removes existing objects and creates new features.

point1_g, point2_g, point3_g = g_i.point((3, 4), (1, 1), (3, 4))

print(g_i.mergeequivalents(point1_g, point3_g))
```

```python
s_i.new()
```

```python
# Alternative 2
# Merges objects with a tolerance. This command removes existing objects and creates new features.

point1_g, point2_g = g_i.point((3, 4), (1, 1))
point3_g, point4_g = g_i.point((3, 4), (1, 1))
point5_g = g_i.point(3, 4)

print(g_i.mergeequivalents(point3_g, point5_g, 1))
```

---

## INPUT: mesh

# Python wrapper commands [MESH]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## mesh
Generates a mesh.

```python
s_i.new()
```

```python
# Alternative 1
# Generates a mesh of the available meshable objects.

g_i.polygon((0, 0), (0, 50), (50, 50), (50, 0))

g_i.gotomesh()
g_i.mesh()
```

```python
# Alternative 2
# Generates a mesh of the available meshable objects with a defined relative element size factor.

g_i.gotomesh()
g_i.mesh(0.1)
```

```python
# Alternative 3
# Generates a mesh of the available meshable objects with a defined relative element size factor and with enhanced mesh refinements.

g_i.gotomesh()
g_i.mesh(0.5, True)
```

---

## INPUT: meshd

# Python wrapper commands [MESHD]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## meshd
Generates a mesh based on element dimension specified in length units rather than as a factor.

```python
s_i.new()
```

```python
# Alternative 1
# Generates a mesh of the available meshable objects.

g_i.polygon((0, 0), (0, 50), (50, 50), (50, 0))
g_i.gotomesh()

g_i.meshd()
```

```python
# Alternative 2
# Generates a mesh of the available meshable objects with specified element dimension.

g_i.gotomesh()
g_i.meshd(1)
```

```python
# Alternative 3
# Generates a mesh of the available meshable objects with specified element dimension and with enhanced mesh refinements

g_i.gotomesh()
g_i.meshd(0.5, True)
```

---

## INPUT: move

# Python wrapper commands [MOVE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## move
Moves an object.

```python
s_i.new()
```

```python
# Alternative 1
# Moves one or more objects in a specified direction.

# Example 1
res = g_i.line((1, 2), "angles", 45, 10, "absolute", (4, 5))
lines_g = [item for item in res if item._plx_type=='Line']

print(g_i.move((lines_g[-2], lines_g[-1]), (0, 1)))

# Example 2
point_g = g_i.point(3, 4)
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((5, 6), (8, 9))[-1]

print(g_i.move((line_g, point_g), (0, 5)))
```

```python
# Alternative 2
# Moves an object in a specified direction.

g_i.gotosoil()
borehole_g = g_i.borehole(0)


borehole_g.move(2, 0)
```

---

## INPUT: movedisconnected

# Python wrapper commands [MOVEDISCONNECTED]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## movedisconnected
Moves an object.

```python
s_i.new()
```

```python
# Alternative 1
# Moves one or more objects in a specified direction.

# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((5, 6), (8, 9))[-1]

# g_i._movedisconnected(line_g, (2, 3))
```

```python
# Alternative 2
# Moves an object in a specified direction.

point_g = g_i.point(2, 2)
# point_g.movedisconnected(0, 5)
```

---

## INPUT: movepoint

# Python wrapper commands [MOVEPOINT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## movepoint
Moves a point of a polygon or water level.

```python
s_i.new()
```

```python
# Alternative 1
# Moves a point of a polygon to another location.
# Creates multiple objects, the first one is the Polygon object ([0])
polygon_g = g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))[0] 

polygon_g.movepoint(3, 6, 2)
```

```python
# Alternative 2
g_i.gotoflow()
waterlevel_s = g_i.waterlevel((0, 2), (2, 3), (3, 3))
waterlevel_s.movepoint(2, 4, 2)
```

---

## INPUT: movepointmagnetic

# Python wrapper commands [MOVEPOINTMAGNETIC]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## movepointmagnetic
Moves a polygon point and the connected objects in a specified direction.

```python
s_i.new()
```

```python
# Alternative 1
# Creates multiple objects, the first one is the Polygon object ([0])
polygon_g = g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))[0]
g_i.movepointmagnetic(polygon_g, 3, 4, 2)
```

---

## INPUT: multiply

# Python wrapper commands [MULTIPLY]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## multiply
Multiplies properties of objects with a specified factor.

```python
s_i.new()
```

```python
# Alternative 1
# Multiplies properties of objects with a specified factor.

point_g = g_i.point(3, 4)
pointload_g = g_i.pointload(point_g)

pointload_g.multiply(4)
```

```python
# Alternative 2
# Multiplies properties of objects with a specified factor.

point1_g, point2_g = g_i.point((1, 2), (2, 2))
line_g = g_i.line(point1_g, point2_g)
lineload_g = g_i.lineload(line_g, "qy_start", 1)

lineload_g.multiply("qy_start", 2)
```

```python
# Alternative 3
# Multiplies properties of objects with a specified factor.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
point_g = g_i.point(3, 9)
pointload_g = g_i.pointload(point_g)
line_g = g_i.line((5, 6), (8, 9))[-1]
lineload_g = g_i.lineload(line_g)

print(g_i.multiply((lineload_g, pointload_g.Fy), 2))

# Example 2
g_i.clear()
point1_g, point2_g = g_i.point((3, 4), (1, 1))
pointload1_g, pointload2_g = g_i.pointload(point1_g, point2_g)
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))

g_i.gotostages()
pointload1_s, pointload2_s = g_i.Pointloads[-2:]
phase0_s = g_i.InitialPhase

print(g_i.multiply((pointload1_s.Fy, pointload2_s.Fy), phase0_s, 2))
```

```python
s_i.new()
```

```python
# Alternative 4
# Multiplies properties of objects with a specified factor.

# Creates multiple objects, the last one is the Line object ([-1])
point_g = g_i.point(5, 2)
pointload_g = g_i.pointload(point_g)
line_g = g_i.line((5, 6), (8, 9))[-1]
lineload_g = g_i.lineload(line_g)

g_i.multiply((lineload_g, pointload_g), 2)
```

```python
# Alternative 5
# Multiplies properties of objects with a specified factor.

point1_g, point2_g = g_i.point((3, 4), (1, 1))
pointload1_g, pointload2_g = g_i.pointload(point1_g, point2_g)

g_i.multiply((pointload1_g, pointload2_g), "Fy", 2)
```

---

## INPUT: n2nanchor

# Python wrapper commands [N2NANCHOR]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## n2nanchor
Adds node-to-node anchor features to lines.

```python
s_i.new()
```

```python
# Alternative 1
# Adds node-to-node anchor features to one or more existing lines in the geometry.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((5, 6), (8, 9))[-1]
n2nanchor_g = g_i.n2nanchor(line_g)
print(n2nanchor_g)

# Example 2
line1_g = g_i.line((0, 2), (-5, 2))[-1]
line2_g = g_i.line((1, 2), "relative", (3, 4))[-1]

n2nanchors_g = g_i.n2nanchor(line1_g, line2_g)
print(n2nanchors_g)

# Example 3
line1_g = g_i.line((5, 9), (8, 8))[-1]
line2_g = g_i.line((1, 2), "relative", (5, 4))[-1]
group_g = g_i.group(line1_g, line2_g)

n2nanchors_g = g_i.n2nanchor(group_g)
print(n2nanchors_g)
```

```python
# Alternative 2
# Creates a line between two points (which may either exist, or will be created) and add a node-to-node anchor feature to it.

# Example 1
# Creates multiple objects, the last one is the NodeToNodeAnchor object ([-1])
point_g = g_i.point(3, 4)
n2nanchor_g = g_i.n2nanchor(point_g, (5, 6))[-1]
print(n2nanchor_g)

# Example 2
point1_g, point2_g = g_i.point((5, 2), (7, 3))
n2nanchor_g = g_i.n2nanchor(point1_g, point2_g)[-1]
print(n2nanchor_g)

# Example 3
n2nanchor_g = g_i.n2nanchor((1, 4), (6, 5))[-1]
print(n2nanchor_g)
```

```python
# Alternative 3
# Creates lines between three or more points (which may either exist, or will be created) and add node-to-node anchor features to them.

point1_g, point2_g = g_i.point((3, 9), (5, 10))

res = g_i.n2nanchor(point1_g, (5.1, 7.2), point2_g)
n2nanchors_g = [item for item in res if item._plx_type == 'NodeToNodeAnchor']
print(n2nanchors_g)
```

```python
# Alternative 4
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect 
# to the xy-plane and a length or a vector describing the direction and a length and add node-to-node anchor features to them.

# Example 1
# Creates multiple objects, the last one is the NodeToNodeAnchor object ([-1])
n2nanchor_g = g_i.n2nanchor((1, 2), "relative", (3, 4))[-1]
print(n2nanchor_g)

# Example 2
point_g = g_i.point(3, 9)
res = g_i.n2nanchor(point_g, "relative", (3, 4), (-5, -9), "angles", 30, 16)
n2nanchors_g = [item for item in res if item._plx_type == 'NodeToNodeAnchor']
print(n2nanchors_g)

# Example 3
res = g_i.n2nanchor((1, 3), "angles", 45, 10, "absolute", (4, 5))
n2nanchors_g = [item for item in res if item._plx_type == 'NodeToNodeAnchor']
print(n2nanchors_g)
```

```python
# Alternative 5
# Adds node-to-node anchor features to one or more existing lines in the geometry and directly set their properties.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((8, 9), (8, 10))[-1]
material_i = g_i.anchormat()
n2nanchor_g = g_i.n2nanchor(line_g, "Material", material_i)
print(n2nanchor_g)

# Example 2
line1_g = g_i.line((3, 7), (5, 6))[-1]
line2_g = g_i.line((4, 2), "relative", (3, 4))[-1]
n2nanchors_g = g_i.n2nanchor((line1_g, line2_g), "Material", material_i)
print(n2nanchors_g)
```

```python
# Alternative 6
# Creates a line between two points (which may either exist, or will be created), add a node-to-node anchor feature to it and directly set its properties.

# Creates multiple objects, the last one is the NodeToNodeAnchor object ([-1])
point_g = g_i.point(3, 4)
n2nanchor_g = g_i.n2nanchor(point_g, (5, 6), "Material", material_i)[-1]
print(n2nanchor_g)
```

```python
# Alternative 7
# Creates lines between three or more points (which may either exist, or will be created), add node-to-node anchor features to them and directly set their properties.

point1_g, point2_g = g_i.point((5, 7), (4, 10))

res = g_i.n2nanchor(point1_g, (5.1, 6.4), point2_g, "Material", material_i)
n2nanchors_g = [item for item in res if item._plx_type == 'NodeToNodeAnchor']
print(n2nanchors_g)
```

```python
# Alternative 8
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect 
# to the xy-plane and a length or a vector describing the direction and a length, add node-to-node anchor features to them and directly set their properties.

# Creates multiple objects, the last one is the NodeToNodeAnchor object ([-1])
n2nanchor_g = g_i.n2nanchor((1, 2), "relative", (3, 8), 
                            "Material", material_i)[-1]
print(n2nanchor_g)

# Obtain Materials assigned for all node to node anchors in a list and display them
anchors_materials_assigned = [material.Name.value for material in g_i.NodeToNodeAnchors.Material.value if material]
print(f'Node-to-node anchor materials assigned: {anchors_materials_assigned}')
```

---

## INPUT: neginterface

# Python wrapper commands [NEGINTERFACE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## neginterface
Adds negative interface features to lines.

```python
s_i.new()
```

```python
# Alternative 1
# Adds negative interface features to one or more existing lines in the geometry.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((5, 6), (8, 9))[-1]
interface_g = g_i.neginterface(line_g)
print(interface_g)

# Example 2
line1_g = g_i.line((0, 2), (-5, 2))[-1]
line2_g = g_i.line((1, 2), "relative", (3, 4))[-1]

interfaces_g = g_i.neginterface(line1_g, line2_g)
print(interfaces_g)

# Example 3
line1_g = g_i.line((5, 9), (8, 8))[-1]
line2_g = g_i.line((1, 2), "relative", (5, 4))[-1]
group_g = g_i.group(line1_g, line2_g)

interfaces_g = g_i.neginterface(group_g)
print(interfaces_g)
```

```python
# Alternative 2
# Creates a line between two points (which may either exist, or will be created) and add a_negative interface feature to it.

# Example 1
# Creates multiple objects, the last one is the NegativeInterface object ([-1])
point_g = g_i.point(3, 4)
interface_g = g_i.neginterface(point_g, (5, 6))[-1]
print(interface_g)

# Example 2
point1_g, point2_g = g_i.point((5, 2), (7, 3))
interface_g = g_i.neginterface(point1_g, point2_g)[-1]
print(interface_g)

# Example 3
interface_g = g_i.neginterface((1, 4), (6, 5))[-1]
print(interface_g)
```

```python
# Alternative 3
# Creates lines between three or more points (which may either exist, or will be created) and add negative interface features to them.

point1_g, point2_g = g_i.point((3, 9), (5, 10))

res = g_i.neginterface(point1_g, (5.1, 7.2), point2_g)
interfaces_g = [item for item in res if item._plx_type == 'NegativeInterface']
print(interfaces_g)
```

```python
# Alternative 4
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect 
# to the xy-plane and a length or a vector describing the direction and a length and add negative interface features to them.

# Example 1
# Creates multiple objects, the last one is the NegativeInterface object ([-1])
interface_g = g_i.neginterface((1, 2), "relative", (3, 4))[-1]
print(interface_g)

# Example 2
point_g = g_i.point(3, 9)
res = g_i.neginterface(point_g, "relative", (3, 4), (-5, -9), "angles", 30, 16)
interfaces_g = [item for item in res if item._plx_type == 'NegativeInterface']
print(interfaces_g)

# Example 3
res = g_i.neginterface((1, 3), "angles", 45, 10, "absolute", (4, 5))
interfaces_g = [item for item in res if item._plx_type == 'NegativeInterface']
print(interfaces_g)
```

```python
# Alternative 5
# Adds negative interface features to one or more existing lines in the geometry and directly set their properties.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((8, 9), (8, 10))[-1]
material_i = g_i.soilmat()
interface_g = g_i.neginterface(line_g, "MaterialMode", "Custom", "Material", material_i)
print(interface_g)

# Example 2
line1_g = g_i.line((3, 7), (5, 6))[-1]
line2_g = g_i.line((4, 2), "relative", (3, 4))[-1]
material_i = g_i.soilmat()
interfaces_g = g_i.neginterface((line1_g, line2_g), "MaterialMode", "Custom", "Material", material_i)
print(interfaces_g)
```

```python
# Alternative 6
# Creates a line between two points (which may either exist, or will be created), add a_negative interface feature to it and directly set its properties.

# Creates multiple objects, the last one is the NegativeInterface object ([-1])
point_g = g_i.point(3, 4)
material_i = g_i.soilmat()
interface_g = g_i.neginterface(point_g, (5, 6), "MaterialMode", "Custom", "Material", material_i)[-1]
print(interface_g)
```

```python
# Alternative 7
# Creates lines between three or more points (which may either exist, or will be created), add negative interface features to them and directly set their properties.

point1_g, point2_g = g_i.point((5, 7), (4, 10))
material_i = g_i.soilmat()
res = g_i.neginterface(point1_g, (5.1, 6.4), point2_g, "MaterialMode", "Custom", "Material", material_i)
interfaces_g = [item for item in res if item._plx_type == 'NegativeInterface']
print(interfaces_g)
```

```python
# Alternative 8
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect 
# to the xy-plane and a length or a vector describing the direction and a length, add negative interface features to them and directly set their properties.

# Creates multiple objects, the last one is the NegativeInterface object ([-1])
material_i = g_i.soilmat()
interface_g = g_i.neginterface((1, 2), "relative", (3, 8), "MaterialMode", "Custom", "Material", material_i)[-1]
print(interface_g)

# Obtain VirtualThicknessFactor property value assigned for all interfaces in a list and display them
interfaces_thicknessfactor = g_i.Interfaces.VirtualThicknessFactor.value
print(f'Interfaces thickness factors: {interfaces_thicknessfactor}')
```

---

## INPUT: phase

# Python wrapper commands [PHASE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## phase
Creates a new phase.

```python
s_i.new()
```

```python
# Alternative 1
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))
g_i.gotostages()
phase0_s = g_i.Phases[0]

phase1_s = g_i.phase(phase0_s)
print(phase1_s)

# Obtain Identification value assigned for all phases in a list and display them
phases_id = g_i.Phases.Identification.value
print(f'Phases Identification property: {phases_id}')
```

---

## INPUT: plate

# Python wrapper commands [PLATE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## plate
Adds plate features to structural surfaces.

```python
s_i.new()
```

```python
# Alternative 1
# Adds plate features to one or more existing lines in the geometry.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])

line_g = g_i.line((5, 6), (8, 9))[-1]
plate_g = g_i.plate(line_g)
print(plate_g)

# Example 2
line1_g = g_i.line((0, 2), (-5, 2))[-1]
line2_g = g_i.line((1, 2), "relative", (3, 4))[-1]

plates_g = g_i.plate(line1_g, line2_g)
print(plates_g)

# Example 3
line1_g = g_i.line((5, 9), (8, 8))[-1]
line2_g = g_i.line((1, 2), "relative", (5, 4))[-1]
group_g = g_i.group(line1_g, line2_g)

plates_g = g_i.plate(group_g)
print(plates_g)
```

```python
# Alternative 2
# Creates a line between two points (which may either exist, or will be created) and add a plate feature to it.

# Example 1
# Creates multiple objects, the last one is the Plate object ([-1])
point_g = g_i.point(3, 4)
plate_g = g_i.plate(point_g, (5, 6))[-1]
print(plate_g)

# Example 2
point1_g, point2_g = g_i.point((5, 2), (7, 3))
plate_g = g_i.plate(point1_g, point2_g)[-1]
print(plate_g)

# Example 3
plate_g = g_i.plate((1, 4), (6, 5))[-1]
print(plate_g)
```

```python
# Alternative 3
# Creates lines between three or more points (which may either exist, or will be created) and add plate features to them.

point1_g, point2_g = g_i.point((3, 9), (5, 10))

res = g_i.plate(point1_g, (5.1, 7.2), point2_g)
plates_g = [item for item in res if item._plx_type == 'Plate']
print(plates_g)
```

```python
# Alternative 4
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect 
# to the xy-plane and a length or a vector describing the direction and a length and add plate features to them.

# Example 1
# Creates multiple objects, the last one is the Plate object ([-1])
plate_g = g_i.plate((1, 2), "relative", (3, 4))[-1]
print(plate_g)

# Example 2
point_g = g_i.point(3, 9)
res = g_i.plate(point_g, "relative", (3, 4), (-5, -9), "angles", 30, 16)
plates_g = [item for item in res if item._plx_type == 'Plate']
print(plates_g)

# Example 3
res = g_i.plate((1, 3), "angles", 45, 10, "absolute", (4, 5))
plates_g = [item for item in res if item._plx_type == 'Plate']
print(plates_g)
```

```python
# Alternative 5
# Adds plate features to one or more existing lines in the geometry and directly set their properties.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((8, 9), (8, 10))[-1]
material_i = g_i.platemat()
plate_g = g_i.plate(line_g, "Material", material_i)
print(plate_g)

# Example 2
line1_g = g_i.line((3, 7), (5, 6))[-1]
line2_g = g_i.line((4, 2), "relative", (3, 4))[-1]
material_i = g_i.platemat()
plates_g = g_i.plate((line1_g, line2_g), "Material", material_i)
print(plates_g)
```

```python
# Alternative 6
# Creates a line between two points (which may either exist, or will be created), add a plate feature to it and directly set its properties.

# Creates multiple objects, the last one is the Plate object ([-1])
point_g = g_i.point(3, 4)
material_i = g_i.platemat()
plate_g = g_i.plate(point_g, (5, 6), "Material", material_i)[-1]
print(plate_g)
```

```python
# Alternative 7
# Creates lines between three or more points (which may either exist, or will be created), add plate features to them and directly set their properties.


point1_g, point2_g = g_i.point((5, 7), (4, 10))
material_i = g_i.platemat()
res = g_i.plate(point1_g, (5.1, 6.4), point2_g, "Material", material_i)
plates_g = [item for item in res if item._plx_type == 'Plate']
print(plates_g)
```

```python
# Alternative 8
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect 
# to the xy-plane and a length or a vector describing the direction and a length, add plate features to them and directly set their properties.

# Creates multiple objects, the last one is the Plate object ([-1])
material_i = g_i.platemat()
plate_g = g_i.plate((1, 2), "relative", (3, 8), "Material", material_i)[-1]
print(plate_g)

# Obtain ApplyStrengthReduction property value assigned for all plates in a list and display them
plates_strength_reduction = g_i.Plates.ApplyStrengthReduction.value
print(f'Plates strength reduction property: {plates_strength_reduction}')
```

---

## INPUT: platemat

# Python wrapper commands [PLATEMAT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## platemat
Creates a plate material set.

```python
s_i.new()
```

```python
# Alternative 1
g_i.platemat()
```

---

## INPUT: point

# Python wrapper commands [POINT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## point
Creates a point.

```python
s_i.new()
```

```python
# Alternative 1
# Creates a point with specified coordinates.

point_g = g_i.point(5, 6)
print(point_g)
```

```python
# Alternative 2
# Creates two or more points with specified coordinates.

points_g = g_i.point((5, 7), (8, 10))
print(points_g)

# Obtain x coordinate value assigned for all points in a list and display them
points_x_value = g_i.Points.x.value
print(f'Points x coordinate value: {points_x_value}')
```

---

## INPUT: pointdispl

# Python wrapper commands [POINTDISPL]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## pointdispl
Adds point prescribed displacement features to points.

```python
s_i.new()
```

```python
# Alternative 1
# Adds point prescribed displacement features to one or more existing points in the geometry.

# Example 1
point_g = g_i.point(3, 4)

pointdisplacement_g = g_i.pointdispl(point_g)
print(pointdisplacement_g)

# Example 2
point1_g, point2_g = g_i.point((5, 2), (7, 3))

pointdisplacements_g = g_i.pointdispl(point1_g, point2_g)
print(pointdisplacements_g)

# Example 3
point1_g, point2_g, point3_g = g_i.point((3, 9), (5, 10), (7, 6))
group_g = g_i.group(point1_g, point2_g, point3_g)

pointdisplacements_g = g_i.pointdispl(group_g)
print(pointdisplacements_g)
```

```python
# Alternative 2
# Creates a new point and add a point prescribed displacement feature to it.

# Creates multiple objects, Point and PointDisplacement objects respectively
point_g, pointdisplacement_g = g_i.pointdispl(5, 7)
print(pointdisplacement_g)
```

```python
# Alternative 3
# Creates several new points and add point prescribed displacement features to them.

res = g_i.pointdispl((5, 7), (8, 10))
pointdisplacements_g = [item for item in res if item._plx_type == 'PointDisplacement']
print(pointdisplacements_g)
```

```python
# Alternative 4
# Adds point prescribed displacement features to one or more existing points in the geometry and directly set their properties.

# Example 1
point_g = g_i.point(3, 9)

pointdisplacement_g = g_i.pointdispl(point_g, "Displacement_x", "Fixed", 
                                     "Displacement_y", "Prescribed")
print(pointdisplacement_g)

# Example 2
point1_g, point2_g = g_i.point((5, 2), (7, 3))

pointdisplacements_g = g_i.pointdispl((point1_g, point2_g), "Displacement_x", "Fixed", 
                                      "Displacement_y", "Prescribed")
print(pointdisplacements_g)
```

```python
# Alternative 5
# Creates a new point, add a point prescribed displacement feature to it and directly set its properties.

# Creates multiple objects, Point and PointDisplacement objects respectively
point_g, pointdisplacement_g = g_i.pointdispl((5, 6), "Displacement_x", "Fixed", 
                                              "Displacement_y", "Prescribed")
print(pointdisplacement_g)
```

```python
# Alternative 6
# Creates several new points, add point prescribed displacement features to them and directly set their properties.

res = g_i.pointdispl((6, 7), (8, 9), "Displacement_x", "Fixed", 
                     "Displacement_y", "Prescribed")
pointdisplacements_g = [item for item in res if item._plx_type == 'PointDisplacement']
print(pointdisplacements_g)

# Obtain uy property value assigned for all point displacements in a list and display them
pointdispls_uy = g_i.PointDisplacements.uy.value
print(f'Point displacements uy property: {pointdispls_uy}')
```

---

## INPUT: pointload

# Python wrapper commands [POINTLOAD]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## pointload
Adds point load features to points.

```python
s_i.new()
```

```python
# Alternative 1
# Adds point load features to one or more existing points in the geometry.

# Example 1
point_g = g_i.point(3, 4)

pointload_g = g_i.pointload(point_g)
print(pointload_g)

# Example 2
point1_g, point2_g = g_i.point((5, 2), (7, 3))

pointloads_g = g_i.pointload(point1_g, point2_g)
print(pointloads_g)

# Example 3
point1_g, point2_g, point3_g = g_i.point((3, 9), (5, 10), (7, 6))
group_g = g_i.group(point1_g, point2_g, point3_g)

pointloads_g = g_i.pointload(group_g)
print(pointloads_g)
```

```python
# Alternative 2
# Creates a new point and add a point load feature to it.

# Creates multiple objects, Point and PointLoad objects respectively
point_g, pointload_g = g_i.pointload(5, 7)
print(pointload_g)
```

```python
# Alternative 3
# Creates several new points and add point load features to them.

res = g_i.pointload((5, 7), (8, 10))
pointloads_g = [item for item in res if item._plx_type == 'PointLoad']
print(pointloads_g)
```

```python
# Alternative 4
# Adds point load features to one or more existing points in the geometry and directly set their properties.

# Example 1
point_g = g_i.point(3, 9)

pointload_g = g_i.pointload(point_g, "Fx", 3, "Fy", 7)
print(pointload_g)

# Example 2
point1_g, point2_g = g_i.point((5, 2), (7, 3))

pointloads_g = g_i.pointload((point1_g, point2_g), "Fx", 3, "Fy", 7)
print(pointloads_g)
```

```python
# Alternative 5
# Creates a new point, add a point load feature to it and directly set its properties.

# Creates multiple objects, Point and PointLoad objects respectively
point_g, pointload_g = g_i.pointload((5, 6), "Fx", 3, "Fy", 7)
print(pointload_g)
```

```python
# Alternative 6
# Creates several new points, add point load features to them and directly set their properties.

res = g_i.pointload((6, 7), (8, 9), "Fx", 3, "Fy", 7)
pointloads_g = [item for item in res if item._plx_type == 'PointLoad']
print(pointloads_g)

# Obtain Force property value assigned for all point loads in a list and display them
pointloads_force = g_i.PointLoads.F.value
print(f'Point Loads F property: {pointloads_force}')
```

---

## INPUT: polycurve

# Python wrapper commands [POLYCURVE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## polycurve
Creates a polycurve.

```python
s_i.new()
```

```python
# Alternative 1
# Creates a polycurve.

polycurve_g = g_i.polycurve(2, 2)
print(polycurve_g)
```

```python
# Alternative 2
# Creates a polycurve and add one or more sections to it.

# Creates multiple objects, the first one is the Polycurve object ([0])
polycurve_g = g_i.polycurve((4, 5), "line", 0, 2, "arc", 45, 90, 3)[0]
print(polycurve_g)
```

---

## INPUT: polygon

# Python wrapper commands [POLYGON]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## polygon
Creates a polygon.

```python
s_i.new()
```

```python
# Alternative 1
# Example 1
# Creates multiple objects, the first one is the Polygon object ([0])
polygon_g = g_i.polygon((3, 2), (4, 5), (10, 11))[0]
print(polygon_g)

# Example 2
point1_g, point2_g, point3_g = g_i.point((1, 1), (2, 5), (6, 8))
polygon_g = g_i.polygon(point1_g, point2_g, point3_g)[0]
print(polygon_g)

# Example 3
point1_g, point2_g = g_i.point((2, 2), (3, 5))
polygon_g = g_i.polygon(point1_g, point2_g, (7, 6), (8, 4))[0]
print(polygon_g)

# Obtain x coordinate value assigned for the first point of all polygons in a list and display them
polygons_firstpoint_x = g_i.Polygons.x.value
print(f'Polygons first point x coordinate: {polygons_firstpoint_x}')
```

---

## INPUT: posinterface

# Python wrapper commands [POSINTERFACE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## posinterface
Adds positive interface features to lines.

```python
s_i.new()
```

```python
# Alternative 1
# Adds positive interface features to one or more existing lines in the geometry.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((5, 6), (8, 9))[-1] 
interface_g = g_i.posinterface(line_g)
print(interface_g)

# Example 2
line1_g = g_i.line((0, 2), (-5, 2))[-1] 
line2_g = g_i.line((1, 2), "relative", (3, 4))[-1] 

interfaces_g = g_i.posinterface(line1_g, line2_g)
print(interfaces_g)

# Example 3
line1_g = g_i.line((5, 9), (8, 8))[-1] 
line2_g = g_i.line((1, 2), "relative", (5, 4))[-1] 
group_g = g_i.group(line1_g, line2_g)

interfaces_g = g_i.posinterface(group_g)
print(interfaces_g)
```

```python
# Alternative 2
# Creates a line between two points (which may either exist, or will be created) and add a_positive interface feature to it.

# Example 1
# # Creates multiple objects, the last one is the PositiveInterface object ([-1])
point_g = g_i.point(3, 4)
interface_g = g_i.posinterface(point_g, (5, 6))[-1]
print(interface_g)

# Example 2
point1_g, point2_g = g_i.point((5, 2), (7, 3))
interface_g = g_i.posinterface(point1_g, point2_g)[-1]
print(interface_g)

# Example 3
interface_g = g_i.posinterface((1, 4), (6, 5))[-1]
print(interface_g)
```

```python
# Alternative 3
# Creates lines between three or more points (which may either exist, or will be created) and add positive interface features to them.

point1_g, point2_g = g_i.point((3, 9), (5, 10))

res = g_i.posinterface(point1_g, (5.1, 7.2), point2_g)
interfaces_g = [item for item in res if item._plx_type == 'PositiveInterface']
print(interfaces_g)
```

```python
# Alternative 4
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect 
# to the xy-plane and a length or a vector describing the direction and a length and add positive interface features to them.

# Example 1
# Creates multiple objects, the last one is the PositiveInterface object ([-1])
interface_g = g_i.posinterface((1, 2), "relative", (3, 4))[-1]
print(interface_g)

# Example 2
point_g = g_i.point(3, 9)
res = g_i.posinterface(point_g, "relative", (3, 4), (-5, -9), "angles", 30, 16)
interfaces_g = [item for item in res if item._plx_type == 'PositiveInterface']
print(interfaces_g)

# Example 3
res = g_i.posinterface((1, 3), "angles", 45, 10, "absolute", (4, 5))
interfaces_g = [item for item in res if item._plx_type == 'PositiveInterface']
print(interfaces_g)
```

```python
# Alternative 5
# Adds positive interface features to one or more existing lines in the geometry and directly set their properties.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((8, 9), (8, 10))[-1] 
material_i = g_i.soilmat()
interface_g = g_i.posinterface(line_g, "MaterialMode", "Custom", "Material", material_i)
print(interface_g)

# Example 2
line1_g = g_i.line((3, 7), (5, 6))[-1] 
line2_g = g_i.line((4, 2), "relative", (3, 4))[-1] 
material_i = g_i.soilmat()
interfaces_g = g_i.posinterface((line1_g, line2_g), "MaterialMode", "Custom", "Material", material_i)
print(interfaces_g)
```

```python
# Alternative 6
# Creates a line between two points (which may either exist, or will be created), add a_positive interface feature to it and directly set its properties.

# Creates multiple objects, the last one is the PositiveInterface object ([-1])
point_g = g_i.point(3, 4)
material_i = g_i.soilmat()
interface_g = g_i.posinterface(point_g, (5, 6), "MaterialMode", "Custom", "Material", material_i)[-1]
print(interface_g)
```

```python
# Alternative 7
# Creates lines between three or more points (which may either exist, or will be created), add positive interface features 
# to them and directly set their properties.

point1_g, point2_g = g_i.point((5, 7), (4, 10))
material_i = g_i.soilmat()
res = g_i.posinterface(point1_g, (5.1, 6.4), point2_g, "MaterialMode", "Custom", "Material", material_i)
interfaces_g = [item for item in res if item._plx_type == 'PositiveInterface']
print(interfaces_g)
```

```python
# Alternative 8
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect 
#to the xy-plane and a length or a vector describing the direction and a length, add positive interface features to them and directly set their properties.

# Creates multiple objects, the last one is the PositiveInterface object ([-1])
material_i = g_i.soilmat()
interface_g = g_i.posinterface((1, 2), "relative", (3, 8), "MaterialMode", "Custom", "Material", material_i)[-1]
print(interface_g)

# Obtain VirtualThicknessFactor property value assigned for all interfaces in a list and display them
interfaces_thicknessfactor = g_i.Interfaces.VirtualThicknessFactor.value
print(f'Interfaces thickness factors: {interfaces_thicknessfactor}')
```

---

## INPUT: predict

# Python wrapper commands [PREDICT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## predict
Predicts whether a command may succeed or fail.

```python
s_i.new()
```

```python
# Alternative 1
# Example 1
print(g_i.predict("echo"))

# Example 2
print(g_i.predict("point (1 2)"))

# Example 3
print(g_i.predict("rename MyNotExistingLine 'line_342'"))
```

---

## INPUT: preview

# Python wrapper commands [PREVIEW]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## preview
View the mesh in a specified phase.

```python
s_i.new()
```

```python
# Alternative 1

# Creates a borehole, adds a soil layer and defines material properties
borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[0].Material = material

# Changes the mode, adds a line load and generates the mesh
g_i.gotostructures()
g_i.lineload((3, 0), (7, 0))

g_i.gotomesh()
g_i.mesh(0.2)

g_i.gotostages()
phase0_s = g_i.InitialPhase

g_i.preview(phase0_s)
```

---

## INPUT: raise

# Python wrapper commands [RAISE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## raise
Generates an error in order to test the error catching functionality.

```python
s_i.new()
```

```python
# Alternative 1
try:
    g_i.raise_()
except:
    print("Exception raised")
```

---

## INPUT: raiseasync

# Python wrapper commands [RAISEASYNC]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## raiseasync
Generates an error in an asynchronous thread in order to test the error catching functionality.

```python
s_i.new()
```

```python
# Alternative 1
try:
    g_i.raiseasync()
except:
    print("Exception Raised")
```

---

## INPUT: raisethreaded

# Python wrapper commands [RAISETHREADED]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## raisethreaded
Generates an error in a synchronous thread in order to test the error catching functionality.

```python
s_i.new()
```

```python
# Alternative 1
try:
    g_i.raisethreaded()
except:
    print("Exception raised")
```

---

## INPUT: rectangle

# Python wrapper commands [RECTANGLE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## rectangle
Creates rectangle.

```python
s_i.new()
```

```python
# Alternative 1

# Example 1
# Creates multiple objects, the first one is the Polygon object ([0])
rectangle_g = g_i.rectangle((0, 1), (2, 3))[0]
print(rectangle_g)

# Example 2
point_g = g_i.point(5, 6)
rectangle_g = g_i.rectangle(point_g, (7, 8))[0]
print(rectangle_g)

# Example 3
point1_g, point2_g = g_i.point((0, 4), (4, 8))
rectangle_g = g_i.rectangle(point1_g, point2_g)[0]
print(rectangle_g)

# Example 4
point_g = (5, 0)
rectangle_g = g_i.rectangle(point_g, (5, 1), (7, 5))[0]
print(rectangle_g)

# Obtain ApplyStrengthReduction property value assigned for all soils in a list and display them
soils_strength_reduction = g_i.Soils.ApplyStrengthReduction.value
print(f'Soils strength reduction property: {soils_strength_reduction}')
```

---

## INPUT: redo

# Python wrapper commands [REDO]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## redo
Redo actions to which undo was applied.

```python
s_i.new()
```

```python
# Alternative 1
# Redo the last action to which undo was applied.

g_i.borehole(1)
g_i.undo()
g_i.redo()
```

```python
# Alternative 2
# Redo one or more actions to which undo was applied.

borehole_g = g_i.borehole(0)
g_i.soillayer(3)
g_i.soillayer(5)
soillayer_g = g_i.Soillayers[-2]
g_i.soillayerheight(borehole_g, soillayer_g, 1)
g_i.undo(4)
g_i.redo(4)
```

---

## INPUT: refine

# Python wrapper commands [REFINE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## refine
Requests a finer mesh for a meshable object.

```python
s_i.new()
```

```python
# Alternative 1
g_i.polygon((0, 0), (0, 2), (2, 2), (2, 0))

g_i.gotomesh()
polygon_s = g_i.Polygons[-1]
g_i.refine(polygon_s)
```

---

## INPUT: regenerate

# Python wrapper commands [REGENERATE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## regenerate
Regenerates the phase settings in one or more phases.

```python
s_i.new()
```

```python
# Alternative 1
# Regenerates the phase settings in one or more staged construction phases.

g_i.polygon((0, 0), (0, 2), (2, 2), (2, 0))
# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((0, 2), (2, 2))[-1] 
line2_g = g_i.line((2, 2), (2, 0))[-1] 
g_i.geogrid(line1_g, line2_g)

g_i.gotostages()
phase1_s = g_i.phase(g_i.Phases[-1])
geogrids_s = g_i.Geogrids

geogrids_s[-1].Active[phase1_s] = True
geogrids_s[-2].Active[phase1_s] = True

g_i.regenerate(geogrids_s[-1], geogrids_s[-2], phase1_s)
```

```python
# Alternative 2
# Regenerates the phase settings in a staged construction phase.

g_i.gotostages()
geogrids_s[-1].Active[phase1_s] = True
geogrids_s[-1].regenerate(phase1_s)
```

---

## INPUT: reinforcement

# Python wrapper commands [REINFORCEMENT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## reinforcement
Adds reinforcement to one or more segments in a tunnel.

```python
s_i.new()
```

```python
# Alternative 1
# Adds rock bolts to a polycurve chain of a tunnel cross section.

tunnel_g = g_i.tunnel((0, 0))
tunnel_g.CrossSection.setproperties("x", 0, "y", 0, 
                                    "ShapeType", "Free", "WholeHalfMode", "Right")
tunnel_g.CrossSection.add("Line", 0, 2, "Arc", 0, 90, 1, "Line", 0, 1, "Arc", 0, 90, 1, "Line", 0, 2)

polycurvechain_g = g_i.polycurvechain(tunnel_g.SliceSegments[0])
rockbolts_g = g_i.reinforcement(polycurvechain_g)
print(rockbolts_g)
```

```python
s_i.new()
```

```python
# Alternative 2
# Adds rock bolts to polycurves of a tunnel cross section.

tunnel_g = g_i.tunnel((0, 0))
tunnel_g.CrossSection.setproperties("x", 0, "y", 0, 
                                    "ShapeType", "Free", "WholeHalfMode", "Right")
tunnel_g.CrossSection.add("Line", 0, 2, "Arc", 0, 90, 1, "Line", 0, 1, "Arc", 0, 90, 1, "Line", 0, 2)
# Creates multiple objects, the last one is the RockBolts object ([-1])
rockbolts_g = g_i.reinforcement(tunnel_g.SliceSegments[-1], tunnel_g.SliceSegments[-2])[-1]
print(rockbolts_g)
```

```python
s_i.new()
```

```python
# Alternative 3
# Adds rock bolts feature to a polycurve chain and directly set their properties.

tunnel_g = g_i.tunnel((0, 0))
tunnel_g.CrossSection.setproperties("x", 0, "y", 0, 
                                    "ShapeType", "Free", "WholeHalfMode", "Right")
tunnel_g.CrossSection.add("Line", 0, 2, "Arc", 0, 90, 1, "Line", 0, 1, "Arc", 0, 90, 1, "Line", 0, 2)

polycurvechain_g = g_i.polycurvechain(tunnel_g.SliceSegments[0])
rockbolts_g = g_i.reinforcement(polycurvechain_g, "Length", 2.0)
print(rockbolts_g)
```

```python
s_i.new()
```

```python
# Alternative 4
# Adds rock bolts feature to one or more polycurve chains and directly set their properties.

tunnel_g = g_i.tunnel((0, 0))
tunnel_g.CrossSection.setproperties("x", 0, "y", 0, 
                                    "ShapeType", "Free", "WholeHalfMode", "Right")
tunnel_g.CrossSection.add("Line", 0, 2, "Arc", 0, 90, 1, "Line", 0, 1, "Arc", 0, 90, 1, "Line", 0, 2)
# Creates multiple objects, the last one is the RockBolts object ([-1])
rockbolts_g = g_i.reinforcement(tunnel_g.SliceSegments[-1], tunnel_g.SliceSegments[-2])[-1]
print(rockbolts_g)
```

---

## INPUT: removeintermediatesteps

# Python wrapper commands [REMOVEINTERMEDIATESTEPS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## removeintermediatesteps
Removes saved intermediate calculation steps.

```python
s_i.new()
```

```python
# Alternative 1
# Removes saved intermediate calculation steps in one or more phases. Only the last calculation step will not be removed.

# Creates a borehole, adds a soil layer and defines material properties
borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[0].Material = material

# Changes the mode, adds a line load and generates the mesh
g_i.gotostructures()
g_i.lineload((3, 0), (7, 0))

g_i.gotomesh()
g_i.mesh(0.1)

# Changes the mode, defines multiple phases and activates the line load
g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
phase1_s.Deform.TimeIntervalSeconds = 0.5
phase1_s.MaxStepsStored = 5
g_i.LineLoads[-1].Active[phase1_s] = True
g_i.calculate()

print(g_i.removeintermediatesteps())
```

```python
s_i.new()
```

```python
# Alternative 2

# Creates a borehole, adds a soil layer and defines material properties
borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[0].Material = material

# Changes the mode, adds a line load and generates the mesh
g_i.gotostructures()
g_i.lineload((3, 0), (7, 0), "qy_start", -100)

g_i.gotomesh()
g_i.mesh(0.1)

# Changes the mode, defines multiple phases and activates the line load
g_i.gotostages()
phase0_s = g_i.InitialPhase
phases_s = [g_i.phase(g_i.Phases[i]) for i in range(5)]

for phase in phases_s:
    phase.DeformCalcType = phase.DeformCalcType.dynamic
    phase.Deform.TimeIntervalSeconds = 0.5
    phase.MaxStepsStored = 5
    g_i.LineLoads[-1].Active[phase] = True

g_i.calculate()

print(g_i.removeintermediatesteps(phase0_s,  phases_s[0], phases_s[-2]))
```

---

## INPUT: rename

# Python wrapper commands [RENAME]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## rename
Renames an object.

```python
s_i.new()
```

```python
# Alternative 1
# Creates multiple objects, the first one is the Polygon object ([0])
polygon_g = g_i.polygon((0, 0), (0, 2), (2, 2), (2, 0))[0]
polygon_g.rename("Wall")
```

---

## INPUT: reportmem

# Python wrapper commands [REPORTMEM]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## reportmem
Reports memory usage.

```python
s_i.new()
```

```python
# Alternative 1
g_i.reportmem()
```

---

## INPUT: reset

# Python wrapper commands [RESET]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## reset
Clears the contents of a polycurve with the option to add one or more new segments.

```python
s_i.new()
```

```python
# Alternative 1
# Clears the contents of a polycurve.

# Creates multiple objects, the first one is the Polycurve object ([0])
polycurve_g = g_i.polycurve((4, 5), "line", 0, 2, "arc", 45, 90, 3)[0]

print(polycurve_g.reset())
```

```python
# Alternative 2
# Clears the contents of a polycurve and add one or more new sections.
polycurve_g = g_i.polycurve((4, 5), "line", 0, 2, "arc", 45, 90, 3)[0]

print(polycurve_g.reset("line", 0, 2))
```

---

## INPUT: resetlocal

# Python wrapper commands [RESETLOCAL]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## resetlocal
Request a reset of the fineness of a mesh.

```python
s_i.new()
```

```python
# Alternative 1
# Creates multiple objects, the first one is the Polygon object ([0])
polygon_g = g_i.polygon((0, 0), (0, 2), (2, 2), (2, 0))[0]

g_i.gotomesh()
polygon_s = g_i.Polygons[-1]
g_i.refine(polygon_s)

g_i.resetlocal(polygon_s)
```

---

## INPUT: retrievesuggestedparameters

# Python wrapper commands [RETRIEVESUGGESTEDPARAMETERS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## retrievesuggestedparameters
Retrieves suggested parameters for a phase.

```python
s_i.new()
```

```python
# Alternative 1
# Creates a borehole, adds a soil layer and defines material properties
borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[0].Material = material

# Changes the mode, adds a line load and generates the mesh
g_i.gotostructures()
g_i.lineload((3, 0), (7, 0))

g_i.gotomesh()
g_i.mesh(0.1)

# Changes the mode, define multiple phases and activates the line load
g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
phase1_s.Deform.TimeIntervalSeconds = 0.5
phase1_s.MaxStepsStored = 5
g_i.LineLoads[-1].Active[phase1_s] = True
g_i.calculate(phase0_s)

g_i.retrievesuggestedparameters(phase1_s)
```

---

## INPUT: rockboltsperpendicular

# Python wrapper commands [ROCKBOLTSPERPENDICULAR]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## rockboltsperpendicular
Adds perpendicular rockbolts to one or more segments in a tunnel.

```python
s_i.new()
```

```python
# Alternative 1
# Adds rock bolts perpendicular to a polycurve chain of a tunnel cross section.

tunnel_g = g_i.tunnel((0, 0))
tunnel_g.CrossSection.setproperties("x", 0, "y", 0, 
                                    "ShapeType", "Free", "WholeHalfMode", "Right")
tunnel_g.CrossSection.add("Line", 0, 2, "Arc", 0, 90, 1, "Line", 0, 1, "Arc", 0, 90, 1, "Line", 0, 2)

polycurvechain_g = g_i.polycurvechain(tunnel_g.SliceSegments[0])
rockbolts_g = g_i.rockboltsperpendicular(polycurvechain_g)
print(rockbolts_g)
```

```python
s_i.new()
```

```python
# Alternative 2
# Adds rock bolts perpendicular to polycurves of a tunnel cross section.

tunnel_g = g_i.tunnel((0, 0))
tunnel_g.CrossSection.setproperties("x", 0, "y", 0, 
                                    "ShapeType", "Free", "WholeHalfMode", "Right")
tunnel_g.CrossSection.add("Line", 0, 2, "Arc", 0, 90, 1, "Line", 0, 1, "Arc", 0, 90, 1, "Line", 0, 2)
# Creates multiple objects, the last one is the RockBoltsPerpendicular object
rockbolts_g = g_i.rockboltsperpendicular(tunnel_g.SliceSegments[-1], tunnel_g.SliceSegments[-2])[-1]
print(rockbolts_g)
```

```python
s_i.new()
```

```python
# Alternative 3
# Adds rock bolts feature to a polycurve chain and directly set their properties.

tunnel_g = g_i.tunnel((0, 0))
tunnel_g.CrossSection.setproperties("x", 0, "y", 0, 
                                    "ShapeType", "Free", "WholeHalfMode", "Right")
tunnel_g.CrossSection.add("Line", 0, 2, "Arc", 0, 90, 1, "Line", 0, 1, "Arc", 0, 90, 1, "Line", 0, 2)

polycurvechain_g = g_i.polycurvechain(tunnel_g.SliceSegments[0])
rockbolts_g = g_i.rockboltsperpendicular(polycurvechain_g, "Length", 2.0)
print(rockbolts_g)
```

```python
s_i.new()
```

```python
# Alternative 4
# Adds rock bolts feature to one or more polycurve chains and directly set their properties.

tunnel_g = g_i.tunnel((0, 0))
tunnel_g.CrossSection.setproperties("x", 0, "y", 0, 
                                    "ShapeType", "Free", "WholeHalfMode", "Right")
tunnel_g.CrossSection.add("Line", 0, 2, "Arc", 0, 90, 1, "Line", 0, 1, "Arc", 0, 90, 1, "Line", 0, 2)
# Creates multiple objects, the last one is the RockBoltsPerpendicular object
rockbolts_g = g_i.rockboltsperpendicular(tunnel_g.SliceSegments[-1], tunnel_g.SliceSegments[-2])[-1]
print(rockbolts_g)
```

---

## INPUT: save

# Python wrapper commands [SAVE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## save
Saves the project.

```python
s_i.new()
```

```python
# Alternative 1
print(g_i.save(r"C:\PLAXIS2D\embankment.p2dx"))
```

```python
# Alternative 2
print(g_i.save())
```

---

## INPUT: selectmeshpoints

# Python wrapper commands [SELECTMESHPOINTS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## selectmeshpoints
Select points-of-interest in the mesh using Output.

```python
s_i.new()
```

```python
# Alternative 1
# Creates a borehole, adds a soil layer and defines material properties
borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[0].Material = material

g_i.gotomesh()
g_i.mesh()

g_i.selectmeshpoints()
```

---

## INPUT: set

# Python wrapper commands [SET]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## set
Changes the properties of an object.

```python
s_i.new()
```

```python
# Alternative 1
# Copies the properties of one object to another.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((3, 7), (5, 6))[-1]
line2_g = g_i.line((4, 2), "relative", (3, 4))[-1]
plate1_g = g_i.plate(line1_g)
material_i = g_i.platemat()
plate2_g = g_i.plate(line2_g, "Material", material_i)

print(plate1_g.set(plate2_g))

# Example 2
point1_g = g_i.point(3, 4)
point2_g = g_i.point(1, 1)

print(point1_g.set(point2_g))
```

```python
# Alternative 2
# Changes a numerical property of an object.

point_g = g_i.point(8, 4)

point_g.x.set(5.2)
```

```python
# Alternative 3
# Changes a numerical property of an object.

point1_g = g_i.point(8, 9)
point2_g = g_i.point(4, 6)

point1_g.x.set(point2_g.x)
```

```python
# Alternative 4
# Changes an integer property of an object.

platematerial_i = g_i.platemat()

platematerial_i.Colour.set(646464)
```

```python
# Alternative 5
# Changes an integer property of an object.

# Example 1
platematerial_i = g_i.platemat()
colours = g_i.Colours

print(platematerial_i.Colour.set(colours.Blue))

# Example 2
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((5, 7), (8, 10))[-1]
well_g = g_i.well(line_g)
print(well_g.Behaviour.set(1))
```

```python
# Alternative 6
# Changes an enumeration property of an object.

# Creates multiple objects, the last one is the Line object ([-1])
line2_g = g_i.line((2, 4), (6, 9))[-1]
line1_g = g_i.line((5, 7), (8, 10))[-1]
well1_g = g_i.well(line1_g, "Behaviour", 1)
well2_g = g_i.well(line2_g)

well2_g.Behaviour.set(well1_g.Behaviour)
```

```python
# Alternative 7
# Changes a text property of an object.

# Creates multiple objects, the last one is the Line object ([-1])
g_i.Project.Title.set("Excavation")
```

```python
s_i.new()
```

```python
# Alternative 8
# Changes a property of an object in one or more phases.

# Creates multiple objects, the last one is the Line object ([-1])
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))
line_g = g_i.line((3, 7), (5, 6))[-1]
platematerial_i = g_i.platemat()
plate_g = g_i.plate(line_g)

g_i.gotostages()
phases_s = [g_i.phase(g_i.Phases[i]) for i in range(3)]
plate_s = g_i.Plates[-1]

plate_s.Material.set((phases_s[1], phases_s[2]), platematerial_i)
```

```python
# Alternative 9
# Changes one or more properties of one or more objects. The properties must be of the same type.

g_i.gotostructures()
point1_g, point2_g, point3_g = g_i.point((3, 4), (1, 1), (0, 0))

g_i.set(point1_g.x, point2_g.y, point3_g.y, 2.0)
```

```python
# Alternative 10 
# Changes a row in an advanced table.

# Example 1
# Clears the geomtery and defines a load multiplier
g_i.clear()
g_i.gotostructures()
loadmultiplier_i = g_i.loadmultiplier()
loadmultiplier_i.Table.add(5, 2)
advancedtablerow = loadmultiplier_i.Table[0]

advancedtablerow.Multiplier.set(345)

# Example 2
displacementmultiplier_i = g_i.displmultiplier()
displacementmultiplier_i.Table.add(6, 4)

displacementmultiplier_i.Table[0][1].set(7)
```

```python
s_i.new()
```

```python
# Alternative 11
# Copies the properties of one phase to the other except the parent phase property. Using this command only copies the phase properties, 
# but does not copy other staged construction settings such as active state of soil and structures, value of loads etc.

# Creates multiple objects, the last one is the Plate object ([-1])
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))
g_i.plate((0, 0), (0, 2))[-1]

g_i.gotostages()
phases_s = [g_i.phase(g_i.Phases[i]) for i in range(3)]

phases_s[1].set(phases_s[2])
```

---

## INPUT: setcolour

# Python wrapper commands [SETCOLOUR]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## setcolour
Changes the colour of a material.

```python
s_i.new()
```

```python
# Alternative 1
# Changes the colour of a material.

platematerial_i = g_i.platemat()
platematerial_i.setcolour(20, 200, 90)
```

```python
# Alternative 2
# Changes the colour of a material.

# Example 1
platematerial_i = g_i.platemat()
platematerial_i.setcolour(646464)

# Example 2
platematerial_i = g_i.platemat()
colours = g_i.Colours
platematerial_i.setcolour(colours.Blue)
```

---

## INPUT: setcurrentphase

# Python wrapper commands [SETCURRENTPHASE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## setcurrentphase
Makes a phase the current phase.

```python
s_i.new()
```

```python
# Alternative 1
# Creates a borehole and adds a soil layer
borehole_g = g_i.borehole(0)
g_i.soillayer(10)

g_i.gotomesh()
g_i.mesh()

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)

g_i.setcurrentphase(phase1_s)
```

---

## INPUT: setdefaultmaterial

# Python wrapper commands [SETDEFAULTMATERIAL]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## setdefaultmaterial
Forces an interface to use the material of the soil it is adjacent to.

```python
s_i.new()
```

```python
# Alternative 1
# Forces the interface of a surface to use the same material as the soil next to which it is located.

borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[-1].Material = material

# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((5, -1), (8, -2))[-1]
interface_g = g_i.posinterface(line_g)
interface_g.setdefaultmaterial()
```

```python
s_i.new()
```

```python
# Alternative 2
# Forces the interface of a surface to use the same material as the soil next to which it is located in one or more phases.

# Creates a broehole, adds a soil layer and defines material properties
borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[-1].Material = material

# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((5, -1), (8, -2))[-1]
interface_g = g_i.posinterface(line_g)

# Changes the mode, generate the mesh and define the phases
g_i.gotomesh()
g_i.mesh()

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
phase2_s = g_i.phase(phase0_s)
interface_s = g_i.Interfaces[-1]

interface_s.setdefaultmaterial(phase0_s, phase2_s)
```

---

## INPUT: setglobalwaterlevel

# Python wrapper commands [SETGLOBALWATERLEVEL]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## setglobalwaterlevel
Changes the global water level.

```python
s_i.new()
```

```python
# Alternative 1
# Sets one water level in a set of water levels to be the global water level in a specified phase.

g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))

g_i.gotoflow()
waterlevel_s = g_i.waterlevel((1, 2), (4, 3))

g_i.gotostages()
phase1_s = g_i.phase(g_i.Phases[-1])

g_i.setglobalwaterlevel(waterlevel_s, phase1_s)
```

---

## INPUT: setmaterial

# Python wrapper commands [SETMATERIAL]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## setmaterial
Assigns a material to features.

```python
s_i.new()
```

```python
# Alternative 1
# Assigns a material to a feature.

# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((5, 6), (8, 9))[-1]
plate_g = g_i.plate(line_g)
platematerial_i = g_i.platemat()

plate_g.setmaterial(platematerial_i)
```

```python
s_i.new()
```

```python
# Alternative 2
# Assigns a material to one or more features.

g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))

# Creates multiple objects, the last one is the Plate object ([-1])
plate1_g = g_i.plate((0, 1), (2, 2))[-1]
plate2_g = g_i.plate((0, 0), (2, 0))[-1]
platematerial_i = g_i.platemat()

print(g_i.setmaterial((plate1_g, plate2_g), platematerial_i))
```

```python
s_i.new()
```

```python
# Alternative 3
# Assigns a material to a feature in one or more phases.

# Example 1
g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))
g_i.geogrid((0, 1), (3, 5))

geogridmaterial_i = g_i.geogridmat()

g_i.gotostages()
phase0_s = g_i.InitialPhase
geogrid_s = g_i.Geogrids[-1]

print(geogrid_s.setmaterial(phase0_s, geogridmaterial_i))

# Example 2
phase1_s = g_i.phase(phase0_s)
phase2_s = g_i.phase(phase0_s)

print(geogrid_s.setmaterial((phase1_s, phase2_s), geogridmaterial_i))
```

```python
s_i.new()
```

```python
# Alternative 4
# Assigns a material to one or more features in one or more phases.

g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))

g_i.gotostructures()
g_i.plate((0, 1), (2, 2))
g_i.plate((0, 0), (2, 0))
platematerial_i = g_i.platemat()

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
phase2_s = g_i.phase(phase0_s)

plates_s = g_i.Plates

print(g_i.setmaterial((plates_s[-2], plates_s[-1]), (phase1_s, phase2_s), platematerial_i))
```

---

## INPUT: setphysicalcpucount

# Python wrapper commands [SETPHYSICALCPUCOUNT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## setphysicalcpucount
Displays or sets the amount of physical and logical CPUs.

```python
s_i.new()
```

```python
# Alternative 1
print(g_i.setphysicalcpucount())
```

```python
# Alternative 2
print(g_i.setphysicalcpucount(3))
```

---

## INPUT: setproperties

# Python wrapper commands [SETPROPERTIES]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## setproperties
Changes properties of objects.

```python
s_i.new()
```

```python
# Alternative 1
# Changes several properties of an object at once.

# Example 1
# Creates multiple objects, the first one is the Polygon object ([0])
polygon_g = g_i.polygon((0, 0), (0, 2), (2, 2), (2, 0))[0]
polygon_g.setproperties("x", 4, "Name", "Building")
print(g_i.echo(polygon_g.x, polygon_g.Name))

# Example 2
point_g = g_i.point(3, 4)
point_g.setproperties("x", 2, "y", 3)
print(point_g.echo())
```

```python
s_i.new()
```

```python
# Alternative 2
# Changes the properties of a feature in a certain phase.

# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((0, 2), (-5, 2))[-1]
anchor_g = g_i.n2nanchor(line_g)
# Creates multiple objects, the first one is the Polygon object ([0])
polygon_g = g_i.polygon((0, 0), (0, 2), (2, 2), (2, 0))[0]

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)

anchor_s = g_i.NodetoNodeAnchors[-1]
anchor_s.setproperties("AdjustPrestress", phase1_s, True)
```

---

## INPUT: setsoillayerlevel

# Python wrapper commands [SETSOILLAYERLEVEL]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## setsoillayerlevel 
Sets the borehole soil layer level.

```python
s_i.new()
```

```python
# Alternative 1
borehole_g = g_i.borehole(1)
g_i.soillayer(3)

g_i.setsoillayerlevel(borehole_g, 0, 6)
```

---

## INPUT: setsoillayerporepressure

# Python wrapper commands [SETSOILLAYERPOREPRESSURE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## setsoillayerporepressure
Changes the pore pressures in a soil layer.

```python
s_i.new()
```

```python
# Alternative 1
borehole_g = g_i.borehole(1)
g_i.soillayer(3)
soillayer_g = g_i.SoilLayers[-1]

g_i.setsoillayerporepressure(borehole_g, soillayer_g, -1, -12)
```

---

## INPUT: settoggle

# Python wrapper commands [SETTOGGLE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## settoggle
Sets a runtime toggle to True or False. This overrides any toggles that have already been specified.

```python
s_i.new()
```

```python
# Alternative 1
g_i.settoggle("DISPLAY_BUILD_IN_CAPTION", True)
```

---

## INPUT: setundostacksize

# Python wrapper commands [SETUNDOSTACKSIZE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## setundostacksize
Displays the amount of actions that can be undone and redone and the maximum revert stack size.

```python
s_i.new()
```

```python
# Alternative 1
# Displays the amount of actions that can be undone and redone and the maximum revert stack size.

print(g_i.setundostacksize())
```

```python
# Alternative 2
# Displays the amount of actions that can be undone and redone and set the maximum revert stack size.

print(g_i.setundostacksize(14))
```

---

## INPUT: setwaterdry

# Python wrapper commands [SETWATERDRY]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## setwaterdry
Sets the pore pressure of one or more soil features to zero.

```python
s_i.new()
```

```python
# Alternative 1
# Sets the pore pressure of one or more soil features to zero in a specified phase.

# Example 1
g_i.polygon((0, 0), (0, 2), (2, 2), (2, 0))

g_i.gotostages()
phase0_s = g_i.InitialPhase
polygon_s = g_i.Polygons[-1]

print(g_i.setwaterdry(polygon_s, phase0_s))

# Example 2
s_i.new()
g_i.polygon((0, 0), (0, 2), (2, 2), (2, 0))
g_i.polygon((2, 0), (2, 2), (4, 2), (4, 0))

g_i.gotostages()
phase0_s = g_i.InitialPhase
polygon1_s = g_i.Polygons[-2]
polygon2_s = g_i.Polygons[-1]

print(g_i.setwaterdry((polygon1_s, polygon2_s), phase0_s))

# Example 3
s_i.new()
g_i.polygon((0, 0), (0, 3), (3, 3), (3, 0))

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
polygon_s = g_i.Polygons[-1]

print(g_i.setwaterdry(polygon_s, phase0_s, phase1_s))
```

```python
s_i.new()
```

```python
# Alternative 2
# Sets the pore pressure of a soil feature to zero in one or more phases.

g_i.polygon((0, 0), (0, 2), (2, 2), (2, 0))

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
soil_s = g_i.Soils[-1]

soil_s.setwaterdry(phase0_s, phase1_s)
```

---

## INPUT: setwaterinterpolate

# Python wrapper commands [SETWATERINTERPOLATE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## setwaterinterpolate
Sets that the pore pressure of one or more soil features should be interpolated.

```python
s_i.new()
```

```python
# Alternative 1
# Sets that the pore pressure of one or more soil features should be interpolated in a specified phase.

# Example 1
g_i.polygon((0, 0), (0, 2), (2, 2), (2, 0))

g_i.gotostages()
phase0_s = g_i.InitialPhase
polygon_s = g_i.Polygons[-1]

print(g_i.setwaterinterpolate(polygon_s, phase0_s))

# Example 2
s_i.new()
g_i.polygon((0, 0), (0, 2), (2, 2), (2, 0))
g_i.polygon((2, 0), (2, 2), (4, 2), (4, 0))

g_i.gotostages()
phase0_s = g_i.InitialPhase
polygon1_s = g_i.Polygons[-2]
polygon2_s = g_i.Polygons[-1]

print(g_i.setwaterinterpolate((polygon1_s, polygon2_s), phase0_s))

# Example 3
s_i.new()
g_i.polygon((0, 0), (0, 3), (3, 3), (3, 0))

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
polygon_s = g_i.Polygons[-1]

print(g_i.setwaterinterpolate(polygon_s, phase0_s, phase1_s))
```

```python
s_i.new()
```

```python
# Alternative 2
# Sets that the pore pressure of a soil features should be interpolated in one or more specified phases.

g_i.polygon((0, 0), (0, 2), (2, 2), (2, 0))

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
soil_s = g_i.Soils[-1]

soil_s.setwaterinterpolate(phase0_s, phase1_s)
```

---

## INPUT: setwaterlevel

# Python wrapper commands [SETWATERLEVEL]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## setwaterlevel
Assigns a water level to one or more objects.

```python
s_i.new()
```

```python
# Alternative 1
# Assigns a water level to one or more objects in a phase.

borehole_g = g_i.borehole(0)
g_i.soillayer(3)
g_i.soillayer(7)

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
soil1_s = g_i.Soils[-1]
soil2_s = g_i.Soils[-2]
waterlevel_s = g_i.waterlevel((1, -2), (3, -2))

g_i.setwaterlevel((soil1_s, soil2_s), (phase0_s, phase1_s), waterlevel_s)
```

```python
s_i.new()
```

```python
# Alternative 2
# Assigns a water level to an object in one or more phases.

borehole_g = g_i.borehole(0)
g_i.soillayer(3)
g_i.soillayer(7)

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
soil1_s = g_i.Soils[-2]
soil2_s = g_i.Soils[-1]
waterlevel_s = g_i.waterlevel((1, -2), (3, -2))

soil2_s.setwaterlevel((phase0_s, phase1_s), waterlevel_s)
```

---

## INPUT: sleep

# Python wrapper commands [SLEEP]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## sleep
This command makes the application to do nothing for the specified number of milliseconds.

```python
s_i.new()
```

```python
# Alternative 1
g_i.sleep(2000)
```

---

## INPUT: snap

# Python wrapper commands [SNAP]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## snap
Snaps geometric objects with a default tolerance value of 0.001 or with an optional tolerance parameter. This command does not remove existing objects, nor creates new geometry, but only adjusts the object position. The arguments are commutative, which implies that they are taken in alphabetical order for snapping regardless of the order of input.

```python
s_i.new()
```

```python
# Alternative 1
# Snaps objects with a default tolerance value of 0.001. This command does not remove existing objects, nor creates new geometry but only adjusts the object position.

point1_g, point2_g = g_i.point((0, 0), (0.001, 0)) 
g_i.snap(point1_g, point2_g)
```

```python
# Alternative 2
# Snaps objects with a tolerance. This command does not remove existing objects, nor creates new geometry but only adjusts the object position.

point1_g, point2_g = g_i.point((2, 0), (2, 1)) 
g_i.snap(point1_g, point2_g, 1)
```

---

## INPUT: snaplinear

# Python wrapper commands [SNAPLINEAR]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## snaplinear
Snaps one or more points that are connected to a line to the object given as argument, in such a way that the orientation of the connected line does not change. This command does not remove existing objects, nor creates new geometry, but only adjusts the object position.

```python
s_i.new()
```

```python
# Alternative 1
point_g = g_i.point(0, 0)
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((0.001, 0), (1, 1))[-1]

g_i.snaplinear(point_g, line_g)
```

---

## INPUT: soillayer

# Python wrapper commands [SOILLAYER]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## soillayer
Adds a soil layer.

```python
s_i.new()
```

```python
# Alternative 1
borehole_g = g_i.borehole(1)
boreholepolygon_g = g_i.soillayer(3)
print(boreholepolygon_g)
```

---

## INPUT: soillayerheight

# Python wrapper commands [SOILLAYERHEIGHT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## soillayerheight
Changes the height of a soil layer.

```python
s_i.new()
```

```python
# Alternative 1
borehole_g = g_i.borehole(1)
g_i.soillayer(3)
soillayer_g = g_i.Soillayers[-1]

g_i.soillayerheight(borehole_g, soillayer_g, 1)
```

---

## INPUT: soilmat

# Python wrapper commands [SOILMAT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## soilmat
Creates a soil material set.

```python
s_i.new()
```

```python
# Alternative 1
g_i.soilmat()
```

---

## INPUT: symmetricclose

# Python wrapper commands [SYMMETRICCLOSE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## symmetricclose
Closes a polycurve symmetrically.

```python
s_i.new()
```

```python
# Alternative 1
# Closes a polycurve symmetrically over the second local axis of the polycurve by adding copies of the existing sections in opposite order. 
# The last point of the polycurve must be located on the local second axis of the polycurve.

# Creates multiple objects, the first one is the Polycurve object ([0])
polycurve_g = g_i.polycurve((0, 0), "line", 0, 2, "line", 90, 2, "line", 90, 2)[0]
segments_g = polycurve_g.symmetricclose()
print(segments_g)
```

```python
# Alternative 2
# Closes a polycurve symmetrically by adding copies of the existing sections in opposite order.

# Example 1
# Creates multiple objects, the first one is the Polycurve object ([0])
polycurve_g = g_i.polycurve((3, 3), "arc", 0, 180, 3)[0]
segment_g = polycurve_g.symmetricclose(True)
print(segment_g)

# Example 2
# Creates multiple objects, the first one is the Polycurve object ([0])
polycurve_g = g_i.polycurve((9, 12), "line", 0, 2, "arc", 0, 180, 2, "line", 0, 2)[0]
segments_g = polycurve_g.symmetricclose(False)
print(segments_g)
```

---

## INPUT: tabulate

# Python wrapper commands [TABULATE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## tabulate
Displays a table of properties for specified objects.

```python
s_i.new()
```

```python
# Alternative 1
# Displays a table with specified objects.

g_i.platemat()
g_i.anchormat()
materiallist_i = g_i.Materials

print(g_i.tabulate(materiallist_i))
```

```python
s_i.new()
```

```python
# Alternative 2
# Displays a table of objects that fulfil a specified criterion.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((0, 2), (-5, 2))[-1]
line2_g = g_i.line((1, 2), "relative", (3, 4))[-1]
platematerial_i = g_i.platemat()
g_i.plate((line1_g, line2_g), "Material", platematerial_i)

print(g_i.tabulate(g_i.Plates, "Material"))

# Example 2
g_i.clear()
# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((5, 6), (8, 9))[-1]
line2_g = g_i.line((1, 2), "relative", (3, 4))[-1]
res = g_i.line((1, 2), "angles", 45, 50, "absolute", (4, 5))
lines_g = [item for item in res if item._plx_type == 'Line']
lines_g = g_i.Lines

print(g_i.tabulate(lines_g, "First Second"))
```

```python
s_i.new()
```

```python
# Alternative 3
# Displays a table (with specified columns) of objects that fulfil a specified criterion.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((5, 6), (8, 9))[-1]
line2_g = g_i.line((1, 2), "relative", (3, 4))[-1]
res = g_i.line((1, 2), "angles", 45, 10, "absolute", (4, 5))
lines_g = [item for item in res if item._plx_type == 'Line']

print(g_i.tabulate(lines_g, "First Second", "First=Point_1"))

# Example 2
g_i.clear()
points_g = g_i.point((3, 4), (2, 5), (2, 7), (5, 6), (6, 7))

print(g_i.tabulate(points_g, "x", "x=2"))

# Example 3
points_g = g_i.Points

print(g_i.tabulate(points_g, " ", "x>2"))

# Example 4
g_i.clear()
g_i.polygon((0, 0), (0, 6), (8, 6), (8, 0))
g_i.gotostages()
phases_s = [g_i.phase(g_i.InitialPhase) for i in range(7)]
g_i.set((phases_s[-1].MaxCores, phases_s[-2].MaxCores, phases_s[-3].MaxCores), 2)
print(g_i.tabulate(phases_s, "Identification DeformCalcType MaxCores", "MaxCores=2"))
```

```python
s_i.new()
```

```python
# Alternative 4
# Displays a table of specified staged construction features in the specified phase.

# Example 1
g_i.polygon((0, 0), (0, 6), (8, 6), (8, 0))
g_i.pointload((2, 0), (2, 2))

# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((0, 2), (2, 2))[-1]
line2_g = g_i.line((2, 2), (2, 0))[-1]
g_i.embeddedbeamrow(line1_g, line2_g)
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)

embeddedbeamrows_s = g_i.EmbeddedBeamRows
print(g_i.tabulate(embeddedbeamrows_s, phase1_s))

# Example 2
pointloads_s = g_i.PointLoads
print(g_i.tabulate(pointloads_s, phase1_s))
```

```python
s_i.new()
```

```python
# Alternative 5
# Displays a table (with specified columns) of staged construction features that are in the specified phase.

# Example 1
g_i.borehole(0)
g_i.soillayer(2)

g_i.pointload((0, 0), (2, 0), (3, 0))

g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)

pointloads_s = g_i.PointLoads
print(g_i.tabulate((pointloads_s[-2], pointloads_s[-1]), phase1_s, "Fx Fz"))

# Example 2
print(g_i.tabulate(pointloads_s, phase1_s, "Fx F Fz"))
```

```python
s_i.new()
```

```python
# Alternative 6
# Displays a table (with specified columns) of staged construction features that are in the specified phase and fulfil the specified criteria.

# Example 1
g_i.borehole(0)
g_i.soillayer(2)

g_i.pointload((0, 0), (2, 0), (3, 0))

g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)

pointloads_s = g_i.PointLoads
pointloads_s[-1].activate(phase1_s)
print(g_i.tabulate((pointloads_s[-2], pointloads_s[-1]), phase1_s, "Fx Fy", "Active=True"))

# Example 2
print(g_i.tabulate(pointloads_s, phase1_s, "Fx F Fy", "Active=False"))
```

```python
s_i.new()
```

```python
# Alternative 7
# Displays a list of phases in which staged construction feature is present.

# Example 1
g_i.borehole(0)
g_i.soillayer(2)

g_i.pointload((0, 0), (2, 0), (3, 0))

g_i.gotostages()
pointload_s = g_i.PointLoads[-1]

phases_s = [g_i.phase(g_i.InitialPhase) for i in range(6)]

print(g_i.tabulate(pointload_s, (phases_s[-3], phases_s[-2])))

# Example 2
print(g_i.tabulate(pointload_s, phases_s))
```

```python
s_i.new()
```

```python
# Alternative 8
# Displays a table (with specified columns) of phases in which staged construction feature is present.

# Example 1
g_i.borehole(0)
g_i.soillayer(2)

g_i.pointload((0, 0), (2, 0), (3, 0))

g_i.gotostages()
pointload_s = g_i.PointLoads[-1]

phases_s = [g_i.phase(g_i.InitialPhase) for i in range(6)]

print(g_i.tabulate(pointload_s, (phases_s[-3], phases_s[-2]), "Fx Fy"))

# Example 2
print(g_i.tabulate(pointload_s, phases_s, "Fx F"))
```

```python
s_i.new()
```

```python
# Alternative 9
# Displays a table (with specified columns) of phases in which staged construction features are present and fulfil the specified criterion.

# Example 1
g_i.borehole(0)
g_i.soillayer(2)

g_i.pointload((0, 0), (2, 0), (3, 0))

g_i.gotostages()
pointload_s = g_i.PointLoads[-1]

phases_s = [g_i.phase(g_i.InitialPhase) for i in range(6)]
pointload_s.activate(phases_s[-2], phases_s[-4])

print(g_i.tabulate(pointload_s, (phases_s[-3], phases_s[-2]), " ", "Active=True"))

# Example 2
print(g_i.tabulate(pointload_s, phases_s, "Fx F Active", "Active=False"))
```

---

## INPUT: temperaturefunction

# Python wrapper commands [TEMPERATUREFUNCTION]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## temperaturefunction
Adds a temperature function.

```python
s_i.new()
```

```python
# Alternative 1
for i in range(3):
    g_i.temperaturefunction()

print(g_i.tabulate(g_i.ThermalFunctions))

# Obtain Signal property value assigned for all head functions in a list and display them
temperaturefunctions_signal = g_i.ThermalFunctions.Signal.value
print(f'Temperature functions signal: {temperaturefunctions_signal}')
```

---

## INPUT: testasync

# Python wrapper commands [TESTASYNC]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## testasync
Tests that asynchronous task execution works correctly.

```python
s_i.new()
```

```python
# Alternative 1
g_i.testasync(30)
```

---

## INPUT: tfbc

# Python wrapper commands [TFBC]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## tfbc
Adds thermal flow boundary condition features to lines.

```python
s_i.new()
```

```python
# Alternative 1
# Adds thermal flow boundary condition features to one or more existing lines in the geometry.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((0, 0), (1, 1))[-1]
thermalflowbc_g = g_i.tfbc(line_g)
print(thermalflowbc_g)

# Example 2
# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((0, 2), (2, 2))[-1]
line2_g = g_i.line((2, 2), (2, 0))[-1]
thermalflowbcs_g = g_i.tfbc(line1_g, line2_g)
print(thermalflowbcs_g)
```

```python
# Alternative 2
# Creates a line between two points (which may either exist, or will be created) and add a thermal flow boundary condition feature to it.

# Example 1
# Creates multiple objects, the last one is the ThermalFlowBC object ([-1])
point_g = g_i.point(0, 0)
thermalflowbc_g = g_i.tfbc(point_g, (5, 6))[-1]
print(thermalflowbc_g)

# Example 2
points_g = g_i.point((1, 1), (1, 4))
line_g, thermalflowbc_g = g_i.tfbc(points_g[-2], points_g[-1])
print(thermalflowbc_g)

# Example 3
# Creates multiple objects, the last one is the ThermalFlowBC object ([-1])
thermalflowbc_g = g_i.tfbc((5, 5), (5, 2))[-1]
print(thermalflowbc_g)
```

```python
# Alternative 3
# Creates lines between three or more points (which may either exist, or will be created) and add thermal flow boundary condition features to them.

points_g = g_i.point((1, 1), (4, 4))
res = g_i.tfbc(points_g[-2], (2, 3), points_g[-1])
thermalflowbcs_g = [item for item in res if item._plx_type == 'ThermalFlowBC']
print(thermalflowbcs_g)
```

```python
# Alternative 4
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect 
# to the xy-plane and a length or a vector describing the direction and a length and add thermal flow boundary condition features to them.

# Example 1
# Creates multiple objects, the last one is the ThermalFlowBC object ([-1])
thermalflowbc_g = g_i.tfbc((1, 2), "relative", (3, 4))[-1]
print(thermalflowbc_g)

# Example 2
point_g = (1, 2)
res = g_i.tfbc(point_g, "relative", (3, 4), (-5, -9), "angles", 30, 16)
thermalflowbcs_g = [item for item in res if item._plx_type == 'ThermalFlowBC']
print(thermalflowbcs_g)

# Example 3
res = g_i.tfbc((1, 2), "angles", 45, 10, "absolute", (4, 5))
thermalflowbcs_g = [item for item in res if item._plx_type == 'ThermalFlowBC']
print(thermalflowbcs_g)
```

```python
# Alternative 5
# Adds thermal flow boundary condition features to one or more existing lines in the geometry and directly set their properties.

# Example 1
# Creates multiple objects, the last one is the ThermalFlowBC object ([-1])
line_g = g_i.line((2, 2), (3, 3))[-1]
thermalflowbc_g = g_i.tfbc(line_g, "Behaviour", "Closed")
print(thermalflowbc_g)

# Example 2
# Creates multiple objects, the last one is the ThermalFlowBC object ([-1])
line1_g = g_i.line((2, 4), (3, 4))[-1]
line2_g = g_i.line((0, 2), (1, 2))[-1]
thermalflowbcs_g = g_i.tfbc(line1_g, line2_g, "Behaviour", "Closed")
print(thermalflowbcs_g)
```

```python
# Alternative 6
# Creates a line between two points (which may either exist, or will be created), add a thermal flow boundary condition feature to it 
# and directly set its properties.

# Creates multiple objects, the last one is the ThermalFlowBC object ([-1])
point_g = g_i.point(1, 1)
thermalflowbc_g = g_i.tfbc(point_g, (5, 6), "Behaviour", "Closed")[-1]
print(thermalflowbc_g)
```

```python
# Alternative 7
# Creates lines between three or more points (which may either exist, or will be created), add thermal flow boundary condition features to them 
# and directly set their properties.

point1_g, point2_g = g_i.point((1, 1), (8, 9))
res = g_i.tfbc(point1_g, (5.1, 6.4), point2_g, "Behaviour", "Closed")
thermalflowbcs_g = [item for item in res if item._plx_type == 'ThermalFlowBC']
print(thermalflowbcs_g)
```

```python
# Alternative 8
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect to the xy-plane 
# and a length or a vector describing the direction and a length, add thermal flow boundary condition features to them and directly set their properties.

# Creates multiple objects, the last one is the ThermalFlowBC object ([-1])
thermalflowbc_g = g_i.tfbc((1, 2), "relative", (3, 4), "Behaviour", "Closed")[-1]
print(thermalflowbc_g)
```

---

## INPUT: tracepoly

# Python wrapper commands [TRACEPOLY]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## tracepoly 
Creates a polygon from two input points and from points along the contour of the existing boundary.

```python
s_i.new()
```

```python
# Alternative 1
# Example 1
g_i.rectangle((0, 0), (1, 1))
# Creates multiple objects, the first one is the Polygon object ([0])
polygon_g = g_i.tracepoly((1, 1), (1, 2))[0]
print(polygon_g)

# Example 2
point_g = (0, 2)
polygon_g = g_i.tracepoly((0, 1), point_g)[0]
print(polygon_g)

# Example 3
polygon_g = g_i.tracepoly((1, 1), (2, 2), (3, 4))[0]
print(polygon_g)
```

---

## INPUT: transferfunction

# Python wrapper commands [TRANSFERFUNCTION]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## transferfunction
Adds a transfer function.

```python
s_i.new()
```

```python
# Alternative 1

for i in range(3):
    g_i.transferfunction()

print(g_i.tabulate(g_i.ThermalFunctions))

# Obtain Signal property value assigned for all head functions in a list and display them
transferfunctions_signal = g_i.ThermalFunctions.Signal.value
print(f'Transfer functions signal: {transferfunctions_signal}')
```

---

## INPUT: transform

# Python wrapper commands [TRANSFORM]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## transform
Multiplies a multiplier by the scaling factor and writes these values into a new column of transformed multiplier. The default scaling factor is 1.0 and it can be modified in DisplacementMultiplier object.

```python
s_i.new()
```

```python
# Alternative 1
displacementmultiplier_g = g_i.displmultiplier()

displacementmultiplier_g.setproperties("Signal", "Table", "DataType", "Accelerations")
displacementmultiplier_g.Table.set(0, 0, 0.25, 1, 0.5, 0, 0.75, -1, 1, 0, 1.25, 1, 1.5, 0, 1.75, -1, 2, 2)
displacementmultiplier_g.ScalingValue = 5
displacementmultiplier_g.transform ()
print(g_i.tabulate(displacementmultiplier_g.Table))
```

---

## INPUT: translateline

# Python wrapper commands [TRANSLATELINE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## translateline
Moves a line of an existing polygon.

```python
s_i.new()
```

```python
# Alternative 1
# Creates multiple objects, the first one is the Polygon object ([0])
polygon_g = g_i.polygon((0, 0), (0, 2), (2, 2), (2, 0))[0]

polygon_g.translateline(3, 2, 1)
```

---

## INPUT: translatelinemagnetic

# Python wrapper commands [TRANSLATELINEMAGNETIC]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## translatelinemagnetic
Moves a line of an existing polygon and the connected polygon(s) in a specified direction.

```python
s_i.new()
```

```python
# Alternative 1
# Creates multiple objects, the first one is the Polygon object ([0])
polygon_g = g_i.polygon((0, 0), (0, 2), (2, 2), (2, 0))[0]

g_i.translatelinemagnetic(polygon_g, 3, 2, 1)
```

---

## INPUT: tunnel

# Python wrapper commands [TUNNEL]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## tunnel
Creates a tunnel at a specified location.

```python
s_i.new()
```

```python
# Alternative 1
tunnel_g = g_i.tunnel(6, 2)
print(tunnel_g)
```

---

## INPUT: undo

# Python wrapper commands [UNDO]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## undo
Undo actions.

```python
s_i.new()
```

```python
# Alternative 1
# Reverses the last action.

g_i.borehole(1)
g_i.undo()
```

```python
# Alternative 2
# Reverses one or more actions.

borehole_g = g_i.borehole(0)
g_i.soillayer(3)
g_i.soillayer(5)
soillayer_g = g_i.Soillayers[-2]
g_i.soillayerheight(borehole_g, soillayer_g, 1)
g_i.undo(4)
```

---

## INPUT: ungroup

# Python wrapper commands [UNGROUP]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## ungroup
Ungroups a group of objects.

```python
s_i.new()
```

```python
# Alternative 1
# Ungroups a group of objects.

point_g = g_i.point(2, 4)
# Creates multiple objects, the first one is the Polygon object ([0])
# Creates multiple objects, the last one is the Line object ([-1])
polygon_g = g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))[0]
line_g = g_i.line((0, 2), (-5, 2))[-1]

group1_g = g_i.group(line_g, polygon_g)
group2_g = g_i.group(polygon_g, point_g)

g_i.ungroup(polygon_g, line_g)
```

```python
# Alternative 2
# Ungroups one or more groups.

# Example 1
# Creates multiple objects, the first one is the Polygon object ([0])
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((5, 6), (8, 10))[-1]
polygon_g = g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))[0]
group_g = g_i.group(line_g, polygon_g)

print(g_i.ungroup(group_g))

# Example 2
# Creates multiple objects, the last one is the Line object ([-1])
line1_g = g_i.line((5, 6), (5, 10))[-1]
line2_g = g_i.line((7, 6), (7, 10))[-1]
line3_g = g_i.line((9, 6), (9, 10))[-1]
line4_g = g_i.line((11, 6), (11, 10))[-1]
building_walls = g_i.group(line1_g, line2_g)
basement_floors = g_i.group(line3_g, line4_g)

print(g_i.ungroup(building_walls, basement_floors))
```

---

## INPUT: view

# Python wrapper commands [VIEW]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## view
Displays the calculation results of a phase.

```python
s_i.new()
```

```python
# Alternative 1
# Creates a borehole, adds a soil layer and defines material properties
borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, "gammaSat", 20, "Gref", 10000)
g_i.Soils[0].Material = material

# Changes the mode, generates the mesh and defines the phases
g_i.gotomesh()
g_i.mesh(0.1)

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
g_i.calculate()

g_i.view(phase1_s)
```

---

## INPUT: viewmesh

# Python wrapper commands [VIEWMESH]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## viewmesh
Displays the generated mesh.

```python
s_i.new()
```

```python
# Alternative 1
# Creates a borehole, adds a soil layer and defines material properties
borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material_i = g_i.soilmat()
material_i.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, "gammaSat", 20, "Gref", 10000)
g_i.Soils[0].Material = material_i

g_i.gotomesh()
g_i.mesh(0.1)

g_i.viewmesh()
```

---

## INPUT: waterlevel

# Python wrapper commands [WATERLEVEL]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## waterlevel
Creates a new water level with one or more points at a specified location.

```python
s_i.new()
```

```python
# Alternative 1
# Creates multiple objects, the first one is the Polygon object ([0])
polygon_g = g_i.polygon((0, 0), (0, 5), (5, 5), (5, 0))[0]

g_i.gotoflow()
waterlevel_s = g_i.waterlevel((0, 2), (5, 3))
print(waterlevel_s)
```

---

## INPUT: well

# Python wrapper commands [WELL]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## well
Adds well features to lines.

```python
s_i.new()
```

```python
# Alternative 1
# Adds well features to one or more existing lines in the geometry.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((0, 0), (1, 1))[-1]
well_g = g_i.well(line_g)
print(well_g)

# Example 2
line1_g = g_i.line((0, 2), (2, 2))[-1]
line2_g = g_i.line((2, 2), (2, 0))[-1]
wells_g = g_i.well(line1_g, line2_g)
print(wells_g)
```

```python
# Alternative 2
# Creates a line between two points (which may either exist, or will be created) and add a well feature to it.

# Example 1
# Creates multiple objects, the last one is the Well object ([-1])
point_g = g_i.point(0, 0)
well_g = g_i.well(point_g, (5, 6))[-1]
print(well_g)

# Example 2
points_g = g_i.point((1, 1), (1, 4))
line_g, well_g = g_i.well(points_g[-2], points_g[-1])
print(well_g)

# Example 3
well_g = g_i.well((5, 5), (5, 2))[-1]
print(well_g)
```

```python
# Alternative 3
# Creates lines between three or more points (which may either exist, or will be created) and add well features to them.

points_g = g_i.point((1, 1), (4, 4))
res = g_i.well(points_g[-2], (2, 3), points_g[-1])
wells_g = [item for item in res if item._plx_type == 'Well']
print(wells_g)
```

```python
# Alternative 4
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect 
# to the xy-plane and a length or a vector describing the direction and a length and add well features to them.

# Example 1
# Creates multiple objects, the last one is the Well object ([-1])
well_g = g_i.well((1, 2), "relative", (3, 4))[-1]
print(well_g)

# Example 2
point_g = (1, 2)
res = g_i.well(point_g, "relative", (3, 4), (-5, -9), "angles", 30, 16)
wells_g = [item for item in res if item._plx_type == 'Well']
print(wells_g)

# Example 3
res = g_i.well((1, 2), "angles", 45, 10, "absolute", (4, 5))
wells_g = [item for item in res if item._plx_type == 'Well']
print(wells_g)
```

```python
# Alternative 5
# Adds well features to one or more existing lines in the geometry and directly set their properties.

# Example 1
# Creates multiple objects, the last one is the Line object ([-1])
line_g = g_i.line((2, 2), (3, 3))[-1]
well_g = g_i.well(line_g, "Behaviour", "Extraction")
print(well_g)

# Example 2
line1_g = g_i.line((2, 4), (3, 4))[-1]
line2_g = g_i.line((0, 2), (1, 2))[-1]
wells_g = g_i.well(line1_g, line2_g, "Behaviour", "Extraction")
print(wells_g)
```

```python
# Alternative 6
# Creates a line between two points (which may either exist, or will be created), add a well feature to it and directly set its properties.

# Creates multiple objects, the last one is the Well object ([-1])
point_g = g_i.point(1, 1)
well_g = g_i.well(point_g, (5, 6), "Behaviour", "Extraction")[-1]
print(well_g)
```

```python
# Alternative 7
# Creates lines between three or more points (which may either exist, or will be created), add well features to them and directly set their properties.

point1_g, point2_g = g_i.point((1, 1), (8, 9))
res = g_i.well(point1_g, (5.1, 6.4), point2_g, "Behaviour", "Extraction")
wells_g = [item for item in res if item._plx_type == 'Well']
print(wells_g)
```

```python
# Alternative 8
# Creates one or more lines by either giving absolute coordinates or relative coordinates, by giving the angles with respect 
# to the xy-plane and a length or a vector describing the direction and a length, add well features to them and directly set their properties.

# Creates multiple objects, the last one is the Well object ([-1])
well_g = g_i.well((1, 2), "relative", (3, 4), "Behaviour", "Extraction")[-1]
print(well_g)

# Obtain Behaviour property value assigned for all wells in a list and display them
wells_behaviour= g_i.Wells.Behaviour.value
print(f'Wells Behaviour property: {wells_behaviour}')
```

---

## INPUT: writephasestomesh

# Python wrapper commands [WRITEPHASESTOMESH]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment.

## writephasestomesh
Writes water and load conditions to files.

```python
s_i.new()
```

```python
# Alternative 1
# Writes the modified parts of the water and load conditions in one or more phases to the files used by the calculation kernel.

borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[-1].Material = material

g_i.gotostructures()
g_i.lineload((3, 0), (7, 0))

g_i.gotomesh()
g_i.mesh(0.1)

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
phase2_s = g_i.phase(phase1_s)
g_i.LineLoads[-1].Active[phase1_s] = True

print(g_i.writephasestomesh(phase0_s, phase2_s))
```

```python
s_i.new()
```

```python
# Alternative 2
# Writes all water and load conditions in one or more phases to the files used by the calculation kernel.

borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[-1].Material = material

g_i.gotostructures()
g_i.lineload((3, 0), (7, 0))

g_i.gotomesh()
g_i.mesh(0.1)

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
phase2_s = g_i.phase(phase1_s)
g_i.LineLoads[-1].Active[phase1_s] = True

g_i.calculate(phase0_s)

print(g_i.writephasestomesh((phase1_s, phase2_s), True))
```

```python
s_i.new()
```

```python
# Alternative 3
# Writes the modified parts of the water and load conditions in all phases to the files used by the calculation kernel.

borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[-1].Material = material

g_i.gotostructures()
g_i.lineload((3, 0), (7, 0))

g_i.gotomesh()
g_i.mesh(0.1)

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
phase2_s = g_i.phase(phase1_s)
g_i.LineLoads[-1].Active[phase1_s] = True

print(g_i.writephasestomesh())
```

```python
s_i.new()
```

```python
# Alternative 4
# Writes all water and load conditions in all phases to the files used by the calculation kernel.

borehole_g = g_i.borehole(0)
g_i.soillayer(10)
material = g_i.soilmat()
material.setproperties("SoilModel", "Linear elastic", "gammaUnsat", 16, 
                       "gammaSat", 20, "Gref", 10000)
g_i.Soils[-1].Material = material

g_i.gotostructures()
g_i.lineload((3, 0), (7, 0))

g_i.gotomesh()
g_i.mesh(0.1)

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)
phase2_s = g_i.phase(phase1_s)
g_i.LineLoads[-1].Active[phase1_s] = True

g_i.calculate()

print(g_i.writephasestomesh(True))
```

---

# PART 2: OUTPUT COMMANDS

Output commands are used with the Output server (g_o, s_o) to
extract results, create plots, and export data after calculation.

## OUTPUT: add

# Python wrapper commands [ADD]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g

    
def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g

def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## add
Adds a certain criteria object to a structural plot.

```python
# Alternative 1
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode and defines the phases
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)
g_i.calculate()
g_i.view(phase1_s)

g_o.cl((0, 0), (1, -2))
g_o.centerline((0, -5), (12, 0))
centerline_o = g_o.CenterLines[-1]

g_o.structuralforcesplot(g_o.Plots[-1])
plot_o = g_o.Plots[-1]

g_o.add(plot_o, centerline_o)
```

---

## OUTPUT: addcurvepoint

# Python wrapper commands [ADDCURVEPOINT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## addcurvepoint
Preselection of stress points or nodes for calculation results, with an indication of a preferred direction.

```python
# Alternative 1
# Preselection of stress points or nodes for calculation results.

s_o, g_o = simple_test_case(s_i, g_i)

g_i.gotostages()

g_i.selectmeshpoints()
g_o.addcurvepoint("node", (3, 0))
```

```python
# Alternative 2
# Preselection of stress points or nodes for calculation results.

g_i.gotostages()

g_i.selectmeshpoints()
g_o.addcurvepoint("node", (4, -2), (0, 1))
```

```python
# Alternative 3
# Preselection of stress points or nodes for calculation results with an indication of a preferred direction for cases 
# with multiple points near the specified coordinates.

s_o, g_o = simple_test_case(s_i, g_i)

g_i.gotostages()
soil_s = g_i.Soils[-1]
# Get the equivalent object in Output
soil_o = get_equivalent(soil_s, g_o)

g_i.selectmeshpoints()
g_o.addcurvepoint("node", soil_o, (5, -5.5))
```

```python
# Alternative 4
# Preselection of stress points or nodes from an entity for calculation results with an indication of a preferred direction for cases 
# with multiple points near the specified coordinates.

s_o, g_o = simple_test_case(s_i, g_i)

g_i.gotostages()
soil_s = g_i.Soils[-1]
# Get the equivalent object in Output
soil_o = get_equivalent(soil_s, g_o)

g_i.selectmeshpoints()
g_o.addcurvepoint("node", soil_o, (4, -5), (0, 1))
```

---

## OUTPUT: allocmem

# Python wrapper commands [ALLOCMEM]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## allocmem
Tests if it is possible to allocate a specific amount of additional memory.

```python
# Alternative 1
s_o, g_o = simple_test_case(s_i, g_i)

try:
    g_o.allocmem(64)
except:
    print("Allocated 64 MB")
```

---

## OUTPUT: apply

# Python wrapper commands [APPLY]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## apply
Applies a command to multiple objects at once.

```python
# Alternative 1
# Applies a command to multiple objects at once. Every time a command is applied to an object an undo-able action is created.
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode and defines the phases
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)

g_i.calculate()
g_i.view(phase1_s)

g_o.centerline((0, -5), (12, 0))
centerlines_o = g_o.CenterLines

print(g_o.apply(centerlines_o, "commands"))
```

```python
# Alternative 2
# Applies a command to multiple objects at once. Every time a command is applied to an object an undo-able action is created.
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode and defines the phases
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)

g_i.calculate()
g_i.view(phase1_s)

g_o.centerline((0, -5), (12, 0))

centerlines_o = g_o.CenterLines
print(g_o.apply(centerlines_o, "setproperties", "Visible", False))
```

---

## OUTPUT: centerline

# Python wrapper commands [CENTERLINE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## centerline
Creates a centerline defined by a sequence of coordinates.

```python
# Alternative 1
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode and defines the phases
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)
g_i.calculate()
g_i.view(phase1_s)

g_o.centerline((0, -5), (12, 0))
```

---

## OUTPUT: centerlineconfig

# Python wrapper commands [CENTERLINECONFIG]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## centerlineconfig
Creates configuration for centerlines.

```python
# Alternative 1
# Creates configuration for centerlines for a material.
s_o, g_o = simple_test_case(s_i, g_i)

material_i = g_i.Materials[-1]

g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)

g_i.calculate()
g_i.view(phase1_s)

material_o = get_equivalent(material_i, g_o)
centerlinecriteriaobject_o = g_o.centerlineconfig(material_o)
print(centerlinecriteriaobject_o)
```

```python
s_i.new()
```

```python
# Alternative 2
# Creates configuration for centerlines for a material with a specified cluster.

# Creates a borehole, adds soil layers and defines material properties
g_i.borehole(0)
g_i.soillayer(5)
g_i.soillayer(10)
material1_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                       "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
material2_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                       "gammaUnsat", 11, "gammaSat", 12, "Gref", 1000)
g_i.Soils[-2].Material = material1_i
g_i.Soils[-1].Material = material2_i
soil_g = g_i.Soils[-1]

# Changes the mode, generates the mesh and defines the phases
g_i.gotomesh()
g_i.mesh(0.1)
g_i.viewmesh()

g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)

g_i.calculate()
g_i.view(phase1_s)

soil_s = g_i.Soils[-1]
material2_o = get_equivalent(material2_i, g_o)
soil_o = get_equivalent(soil_s, g_o)

centerlinecriteriaobject_o = g_o.centerlineconfig(material2_o, soil_o)
print(centerlinecriteriaobject_o)
```

---

## OUTPUT: clearcurvepoints

# Python wrapper commands [CLEARCURVEPOINTS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## clearcurvepoints
Clears the preselected curve points.

```python
# Alternative 1
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode, defines the phases, and adds curvepoints
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)

for i in range (6):
    g_o.addcurvepoint("node", (i/2, -i/2))
    
print(g_o.echo(g_o.CurvePoints.Nodes))

# Obtain y coordinate of all Curvepoints in a list and display them
curvepoints_y = g_o.Curvepoints.y.value
print(f'Curvepoints y coordinates: {curvepoints_y}')

g_o.clearcurvepoints()
print(g_o.echo(g_o.CurvePoints.Nodes))
```

---

## OUTPUT: close

# Python wrapper commands [CLOSE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## close
Closes output.

```python
# Alternative 1
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode and defines the phases
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)

g_i.calculate()
g_i.view(phase1_s)

g_o.close()
```

---

## OUTPUT: commands

# Python wrapper commands [COMMANDS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## commands
Displays available commands and their signatures.

```python
# Alternative 1
# Displays all available global commands for the current working mode with their corresponding signature(s).

s_o, g_o = simple_test_case(s_i, g_i)

print(g_o.commands())
```

```python
# Alternative 2
# Displays the signatures of one or more global commands.

# Example 1
print(g_o.commands("rename"))

# Example 2
print(g_o.commands("get"))
```

```python
# Alternative 3
# Displays all available commands for a listable object with their signatures.

s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode and defines the phases
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)
g_i.calculate()
g_i.view(phase1_s)

g_o.centerline((0, -5), (12, 0))
centerline_o = g_o.CenterLines[-1]

print(g_o.commands(centerline_o.Points))
```

```python
# Alternative 4
# Displays the signatures of one or more global commands for a listable object.

print(g_o.commands(centerline_o.Points, "m"))
```

---

## OUTPUT: count

# Python wrapper commands [COUNT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## count
Displays the number of objects of a specified type that are present.

```python
# Alternative 1
# Counts the number of values in an object.
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode, defines the phases, adds a curvepoint and activates the line loads
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)

g_i.selectmeshpoints()
curvepoint_o = g_o.addcurvepoint("node", (8, -1))
g_o.update()

g_i.LineLoads.activate(phase1_s)
g_i.calculate()
g_i.view(phase1_s)

values_o = g_o.getresults(g_o.ResultTypes.Soil.Ux, "node")

g_o.count(values_o)
```

```python
# Alternative 2
# Counts the number of values in an object which fulfill a specified criterion.
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode and defines the phases
g_i.gotostages()
phases_s = [g_i.phase(g_i.phases[0]) for i in range(4)]

g_i.calculate()
g_i.view(phases_s[-1])

phases_o = g_o.Phases
g_o.count(phases_o, "Info.Maxcores=1")
```

---

## OUTPUT: delete

# Python wrapper commands [DELETE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## delete
Deletes a plot or centerline.

```python
# Alternative 1
# Deletes a plot.
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode and defines the phases
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)

g_i.calculate()
g_i.view(phase1_s)

plot_o = g_o.Plots[-1]
g_o.structuralforcesplot(plot_o)
g_o.delete(plot_o)
```

```python
# Alternative 2
# Deletes a centerline.
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode and defines the phases
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)
g_i.calculate()
g_i.view(phase1_s)

g_o.centerline((0, -5), (12, 0))
g_o.centerline((0, -4), (7, 0))

centerline_o = g_o.CenterLines[-1]

g_o.delete(centerline_o)
```

---

## OUTPUT: dump

# Python wrapper commands [DUMP]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## dump
Displays the details of the project.

```python
# Alternative 1
s_o, g_o = simple_test_case(s_i, g_i)

g_o.dump()
```

---

## OUTPUT: dumpdisplacements

# Python wrapper commands [DUMPDISPLACEMENTS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## dumpdisplacements
Displays a list of all prescribed displacements.

```python
# Alternative 1
# Displays a list of all prescribed displacements.
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode, defines line displacements and generates the mesh
g_i.gotostructures()
g_i.linedispl((0, 0), (0, 2))
g_i.linedispl((4, 0), (9, 0))

g_i.gotomesh()
g_i.mesh(0.1)

# Changes the mode, defines the phases and activates the line displacements
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)

g_i.LineDisplacements.activate(phase1_s)
g_i.calculate()
g_i.view(phase1_s)

phase1_o = get_equivalent(phase1_s, g_o)
g_o.dumpdisplacements(phase1_o)
```

```python
# Alternative 2
# Displays a list of all prescribed displacements for a phase at specific coordinates.
g_o.dumpdisplacements(phase1_o, (4, 0))
```

```python
# Alternative 3
# Displays a list of all prescribed displacements for a phase with a specific criterion such as position, displacement or reaction force.
g_o.dumpdisplacements(phase1_o, 'position', 'displacement')
```

---

## OUTPUT: dumpfixities

# Python wrapper commands [DUMPFIXITIES]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## dumpfixities
Displays a list of all fixities.

```python
# Alternative 1
# Displays a list of all fixities.
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode and defines the phases
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)

g_i.calculate()
g_i.view(phase1_s)

phase1_o = get_equivalent(phase1_s, g_o)
g_o.dumpfixities(phase1_o)
```

```python
# Alternative 2
# Displays a list of all fixities for a phase at specific coordinates.
g_o.dumpfixities(phase1_o, (0, 0))
```

```python
# Alternative 3
# Displays a list of all fixities for a phase for position, x, y or rotational fixity.
g_o.dumpfixities(phase1_o, 'position', 'x')
```

```python
# Alternative 4
# Displays a list of all fixities for a phase for x, y or rotational fixity at specific coordinates.
g_o.dumpfixities(phase1_o, 'position', 'x', (0, 0))
```

---

## OUTPUT: dumpfrostlines

# Python wrapper commands [DUMPFROSTLINES]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    return s, g
```

## dumpfrostlines
Displays a list of all frost line segments.

```python
# Alternative 1
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode and defines the phases
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)

g_i.preview(phase1_s)

phase1_o = get_equivalent(phase1_s, g_o)
g_o.dumpfrostlines(phase1_o)
```

---

## OUTPUT: dumpphreaticlevels

# Python wrapper commands [DUMPPHREATICLEVELS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    return s, g
```

## dumpphreaticlevels 
Displays a list of all phreatic level segments, where each segment is shown as a pair of positions.

```python
# Alternative 1
s_o, g_o = suction_test_case(s_i, g_i)

g_i.gotostages()

g_i.calculate()
phase0_s = g_i.Phases[0] 
g_i.view(phase0_s)

g_o.dumpphreaticlevels(phase0_s)
```

---

## OUTPUT: dumpwaterloads

# Python wrapper commands [DUMPWATERLOADS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    return s, g
```

## dumpwaterloads
Displays a list of all water loads.

```python
# Alternative 1
# Displays a list of all water loads.
s_o, g_o = dynamic_test_case(s_i, g_i)

# Changes the mode, defines the phases and activates the line loads
g_i.gotostages()
phase1_s = g_i.Phases[-1]
g_i.LineLoads.activate(phase1_s)    


g_i.calculate()
g_i.view(phase1_s)

phase1_o = get_equivalent(phase1_s, g_o)
g_o.dumpwaterloads(phase1_o)
```

```python
# Alternative 2
# Displays a list of all water loads for a phase at a specific coordinate.

g_o.dumpwaterloads(phase1_o, (0, -2))
```

```python
# Alternative 3
# Displays a list of water loads or the number of water loads for a specific phase.

g_o.dumpwaterloads(phase1_o, 'count')
```

---

## OUTPUT: echo

# Python wrapper commands [ECHO]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## echo
Displays the details of an object.

```python
# Alternative 1
# Displays extended details of all phases.
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode and defines the phases
g_i.gotostages()
phases_s = [g_i.phase(g_i.phases[0]) for i in range(4)]

g_i.calculate()
g_i.view(phases_s[-1])

phases_o = g_o.Phases

print(g_o.echo(phases_o))
```

```python
# Alternative 2
# Displays details of a specified object.
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode, defines the phases, adds a curvepoint and activates the line loads
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)
curvepoint_o = g_o.addcurvepoint("node", (3, -1))
g_o.update()
g_i.LineLoads.activate(phase1_s)

g_i.calculate()
g_i.view(phase1_s)

phase1_o = g_o.Phases[-1]
utotresults_o = g_o.getresults(phase1_o, g_o.ResultTypes.Soil.Utot, "node", True)
result_o = utotresults_o.filter("max")
result_o.echo()
```

---

## OUTPUT: export

# Python wrapper commands [EXPORT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## export
Exports a plot.

```python
# Alternative 1
# Exports the last created plot to a specified location.
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode and defines the phases
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)

g_i.calculate()
g_i.view(phase1_s)

g_o.Plots[-1].export("C:\data\image.png")
```

```python
# Alternative 2
# Exports a plot to a specified location and with a specific size.
g_i.gotostages()

g_o.Plots[-1].export("C:\data\image.png", 1920, 1080)
```

---

## OUTPUT: filter

# Python wrapper commands [FILTER]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## filter
Filters a list of specified objects.

```python
# Alternative 1
# Shows the contents of a list of objects.
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode and defines the phases
g_i.gotostages()
phases_s = [g_i.phase(g_i.phases[0]) for i in range(4)]

g_i.calculate()
g_i.view(phases_s[-1])

g_o.filter(phases_s)
```

```python
# Alternative 2
# Shows the item at the specified index in a listable.
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode and defines the phases
g_i.gotostages()
phases_s = [g_i.phase(g_i.phases[0]) for i in range(4)]
phases_s[-1].MaxCores = 3
phases_s[-2].MaxCores = 1

g_i.calculate()
g_i.view(phases_s[-1])

g_o.filter(phases_s, "info.MaxCores<4")
```

```python
# Alternative 3
# Shows a list of objects that fulfill a specified criterion.
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode and defines the phases
g_i.gotostages()
phases_s = [g_i.phase(g_i.phases[0]) for i in range(4)]

g_i.calculate()
g_i.view(phases_s[-1])

g_o.filter(phases_s, 1)
```

```python
# Alternative 4
# Shows a list of objects that fulfill a specified criterion.
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode and defines the phases
g_i.gotostages()
phases_s = [g_i.phase(g_i.phases[0]) for i in range(4)]

g_i.calculate()
g_i.view(phases_s[-1])

g_o.filter(phases_s, 2, 4)
```

```python
# Alternative 5
# Shows a list of objects that fulfill a specified criterion.
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode, defines the phases and adds a curvepoint
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)
curvepoint_o = g_o.addcurvepoint("node", (3, 0))
g_o.update()

g_i.calculate()
g_i.view(phase1_s)

utotresults_o = g_o.getresults(phase1_s, g_o.ResultTypes.Soil.Utot, "node", True)
utotresults_o.filter("max")
```

```python
# Alternative 6
# Shows a list of objects that fulfill a specified criterion at a specific index.
s_o, g_o = simple_test_case(s_i, g_i)

g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)
curvepoint_o = g_o.addcurvepoint("node", (5, 0))
g_o.update()

g_i.calculate()
g_i.view(phase1_s)

utotresults_o = g_o.getresults(phase1_s, g_o.ResultTypes.Soil.Utot, "node", True)
utotresults_o.filter("max", 2)
```

---

## OUTPUT: generate

# Python wrapper commands [GENERATE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## generate
Generates a centerline.

```python
# Alternative 1
s_o, g_o = simple_test_case(s_i, g_i)
material_i = g_i.Materials[-1]

# Changes the mode and defines the phases
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)

g_i.calculate()
g_i.view(phase1_s)
phase1_o = g_o.Phases[1]
material_o = get_equivalent(material_i)

centerlinecriteriaobject_o = g_o.centerlineconfig(material_o)
g_o.generate(phase1_o, centerlinecriteriaobject_o)
```

---

## OUTPUT: getcurveresults

# Python wrapper commands [GETCURVERESULTS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    return s, g
```

## getcurveresults
Displays results for curve points that have been previously selected.

```python
# Alternative 1
# Displays results for curve points that have been previously selected.

# Example 1
s_o, g_o = dynamic_test_case(s_i, g_i)

# Changes the mode, defines the phases, adds a curvepoint and activates the line loads
g_i.gotostages()
phase1_s = g_i.Phases[-1]

g_i.selectmeshpoints()
g_o.addcurvepoint("node", (3, 0))
g_o.update()

g_i.LineLoads.activate(phase1_s)

g_i.calculate()
g_i.view(phase1_s)

phase1_o = get_equivalent(phase1_s, g_o)
curvepoint_o = g_o.CurvePoints.Nodes[-1]

uy_o = g_o.getcurveresults(curvepoint_o, phase1_o, g_o.ResultTypes.Soil.Uy)
print(uy_o)

# Example 2
g_i.selectmeshpoints()
g_o.addcurvepoint("node", (6, -1))
g_o.update()

curvepoint_o = g_o.CurvePoints.Nodes[-1]
print(g_o.getcurveresults(curvepoint_o, g_o.Steps[-3], g_o.ResultTypes.Soil.Uy))
```

```python
# Alternative 2
# Displays results for curve points that have been previously selected with minimum, maximum or last values.

# Example 1
s_o, g_o = dynamic_test_case(s_i, g_i)

# Changes the mode, defines the phases, adds a curvepoint and activates the line loads
g_i.gotostages()
phase1_s = g_i.Phases[-1]

g_i.selectmeshpoints()
g_o.addcurvepoint("node", (5, 0))
g_o.update()

g_i.LineLoads.activate(phase1_s)

g_i.calculate()
g_i.view(phase1_s)

g_o.addcurvepoint("node", (4, -1))
phase1_o = get_equivalent(phase1_s, g_o)

ux_o = g_o.getcurveresults(g_o.PostCalcNodes[-1], phase1_o, g_o.ResultTypes.Soil.Ux)
print(ux_o)

# Example 2

curvepoint_o = g_o.CurvePoints.Nodes[-1]
print(g_o.getcurveresults(curvepoint_o, g_o.Steps[-1], g_o.ResultTypes.Soil.Uy))
```

---

## OUTPUT: getcurveresultspath

# Python wrapper commands [GETCURVERESULTSPATH]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    return s, g
```

## getcurveresultspath
Displays results for curve points that have been previously selected for several different phases.

```python
# Alternative 1
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode, defines the phases, adds a curvepoint and activates the line loads
g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)

g_i.selectmeshpoints()
g_o.addcurvepoint("node", (3, 0))
g_o.update()

g_i.LineLoads.activate(phase1_s)

g_i.calculate()
g_i.view(phase1_s)

# Get equivalent object in Output
phase0_o = get_equivalent(phase0_s, g_o)
phase1_o = get_equivalent(phase1_s, g_o)

curvepoint_o = g_o.CurvePoints.Nodes[-1]

value_o = g_o.getcurveresultspath(curvepoint_o, phase0_o, phase1_o, g_o.ResultTypes.Soil.Utot)
print(value_o, value_o.echo())
```

---

## OUTPUT: getresults

# Python wrapper commands [GETRESULTS]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    return s, g
```

## getresults
Generates a table with the calculation results.

```python
# Alternative 1
# Generates a table with the calculation results of a specified block in a phase.
s_o, g_o = suction_test_case(s_i, g_i)

# Changes the mode, defines the phases, adds a waterlevel and adds a curvepoint
g_i.gotostages()
phase0_s = g_i.InitialPhase
waterlevel_s = g_i.waterlevel((0, 1.5), (10,1.5))
g_i.Water.GlobalWaterLevel.set(phase0_s, waterlevel_s)

g_i.selectmeshpoints()
g_o.addcurvepoint("stresspoint", (4, 1.8))
g_o.update()

g_i.calculate()
g_i.view(phase0_s)

phase0_o = g_o.Phases[0]
values_o = g_o.getresults(phase0_o, g_o.ResultTypes.Soil.Suction, "stresspoint")
print(values_o, values_o.echo())
```

```python
# Alternative 2
# Generates a table with the calculation results of a specified block in a phase.
phase0_s = g_i.Phases[0]
g_i.view(phase0_s)

phase0_o = get_equivalent(phase0_s, g_o)

values_o = g_o.getresults(phase0_o, g_o.ResultTypes.Soil.Suction, "node", True)
print(values_o, values_o.echo())
```

```python
# Alternative 3
# Generates a table with the calculation results of a specified block in a phase.
s_o, g_o = embeddedbeam_test_case(s_i, g_i)

# Changes the mode, defines the phases, adds a curvepoint and activates the line loads, embedded beams
g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)

g_i.selectmeshpoints()
curvepoint_o = g_o.addcurvepoint("node", (8, -1))
g_o.update()
g_i.LineLoads.activate(phase1_s)
g_i.EmbeddedBeamRows.activate(phase1_s)

g_i.calculate()
g_i.view(phase1_s)
phase1_o = get_equivalent(phase1_s, g_o)

values_o = g_o.getresults(phase1_o, g_o.ResultTypes.EmbeddedBeamRow.Utot, "node")
print(values_o, values_o.echo())
```

```python
# Alternative 4
# Generates a table with the calculation results of a specified block in a phase.
g_i.gotostages()
phase1_s = g_i.Phases[-1]
g_i.view(phase1_s)

phase1_o = get_equivalent(phase1_s, g_o)

values_o = g_o.getresults(phase1_o, g_o.ResultTypes.EmbeddedBeamRow.Utot, "node", True)
print(values_o, values_o.echo())
```

```python
# Alternative 5
# Generates a table with the calculation results of a specified centerline in a phase.
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode, defines the phases and activates the line loads
g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)

g_i.LineLoads.activate(phase1_s)

g_i.calculate()
g_i.view(phase1_s)

g_o.centerline((3, -1), (10, -1))
g_o.sfplt(g_o.Plots[-1])

g_o.add(g_o.Plots[-1], g_o.Centerlines[-1])

phase1_o = g_o.Phases[1]
values_o = g_o.getresults(g_o.CenterLines[-1], phase1_o, g_o.ResultTypes.CenterLine.M2D)
print(values_o, values_o.echo())
```

```python
# Alternative 6
# Generates a table with the calculation results of a specified block for the active phase.
g_i.gotostages()
phase1_s = g_i.Phases[-1]
g_i.view(phase1_s)

values_o = g_o.getresults(g_o.ResultTypes.Soil.Ux, "node")
print(values_o, values_o.echo())
```

```python
# Alternative 7
# Generates a table with the calculation results of a specified block for the active phase.
g_i.gotostages()
phase1_s = g_i.Phases[-1]
g_i.view(phase1_s)

values_o = g_o.getresults(g_o.ResultTypes.Soil.Utot, "node", True)
print(values_o, values_o.echo())
```

```python
# Alternative 8
# Generates a table with the calculation results of a specified block for the active phase.
s_o, g_o = embeddedbeam_test_case(s_i, g_i)

# Changes the mode, defines the phases, adds a curvepoint and activates the line loads, embedded beams
g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)

g_i.selectmeshpoints()
curvepoint_o = g_o.addcurvepoint("node", (8, -1))
g_o.update()

g_i.LineLoads.activate(phase1_s)
g_i.EmbeddedBeamRows.activate(phase1_s)

g_i.calculate()
g_i.view(phase1_s)

embeddedbeamrow_s = g_i.EmbeddedBeamRows[-1]
embeddedbeamrow_o = get_equivalent(embeddedbeamrow_s, g_o)

values_o = g_o.getresults(embeddedbeamrow_o, g_o.ResultTypes.EmbeddedBeamRow.Utot, "node")
print(values_o, values_o.echo())
```

```python
# Alternative 9
# Generates a table with the calculation results of a specified block for the active phase.
g_i.gotostages()
phase1_s = g_i.Phases[-1]
g_i.view(phase1_s)

embeddedbeamrow_s = g_i.EmbeddedBeamRows[-1]
embeddedbeamrow_o = get_equivalent(embeddedbeamrow_s)

values_o = g_o.getresults(embeddedbeamrow_o, g_o.ResultTypes.EmbeddedBeamRow.Utot, "node", True)
print(values_o, values_o.echo())
```

---

## OUTPUT: getsingleresult

# Python wrapper commands [GETSINGLERESULT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    return s, g
```

## getsingleresult
Gives the result at the specified coordinate or a specific node/stress point with or without result smoothing.

```python
# Alternative 1
# Gives the result at a specific node or stress point.
s_o, g_o = suction_test_case(s_i, g_i)

# Adds a curvepoint, changes the mode and defines the phases
g_i.selectmeshpoints()
g_o.addcurvepoint("node", (4, 1.8))
g_o.update()

g_i.gotostages()
phase0_s = g_i.InitialPhase

g_i.calculate()
g_i.view(phase0_s)

phase0_o = g_o.Phases[0]
curvepoint_o = g_o.CurvePoints.Nodes[-1]

value_o = g_o.getsingleresult(phase0_o, g_o.ResultTypes.Soil.Suction, curvepoint_o)
print(value_o)
```

```python
# Alternative 2
# Gives the result at a specific node or stress point with or without result smoothing.

value_o = g_o.getsingleresult(phase0_o, g_o.ResultTypes.Soil.Suction, curvepoint_o, True)
print(value_o)
```

```python
# Alternative 3
# Gives the result at a specified coordinate

value_o = g_o.getsingleresult(phase0_o, g_o.ResultTypes.Soil.Suction, (4, 1.6))
print(value_o)
```

```python
# Alternative 4
# Gives the result at a specified coordinate with or without result smoothing.

value_o = g_o.getsingleresult(phase0_o, g_o.ResultTypes.Soil.Suction, (4, 1.6), False)
print(value_o)
```

```python
# Alternative 5
# Gives the result at a specified coordinate with or without result smoothing along a preferred direction.

value_o = g_o.getsingleresult(phase0_o, g_o.ResultTypes.Soil.Suction, (4, 1.4), True, (1, 0))
print(value_o)
```

```python
# Alternative 6
# Gives the result at a specified coordinate on the update geometry of the mesh with or without result smoothing along a preferred direction.

value_o = g_o.getsingleresult(phase0_o, g_o.ResultTypes.Soil.Suction, (4, 1.3), True, (1, 0), True)
print(value_o)
```

---

## OUTPUT: hide

# Python wrapper commands [HIDE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## hide
Hides elements in a plot.

```python
# Alternative 1
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode, defines the phases, and activates the line loads
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)
lineload_s = g_i.LineLoads[-1]
lineload_s.activate(phase1_s)

g_i.calculate()
g_i.view(phase1_s)

# Get the equivalent object in Output
lineload_o = get_equivalent(lineload_s, g_o)
g_o.Plots[-1].hide(lineload_o)
```

---

## OUTPUT: index

# Python wrapper commands [INDEX]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## index
Displays the value at the given index.

```python
# Alternative 1
s_o, g_o = embeddedbeam_test_case(s_i, g_i)

# Changes the mode, define the phases, adds a curvepoint and activate the lineloads and embedded beams
g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)

g_i.selectmeshpoints()
g_o.addcurvepoint("node", (8, -1))
g_o.update()
g_i.LineLoads.activate(phase1_s)
g_i.EmbeddedBeamRows.activate(phase1_s)

g_i.calculate()
g_i.view(phase1_s)

embeddedbeamrow_s = g_i.EmbeddedBeamRows[-1]
embeddedbeamrow_o = get_equivalent(embeddedbeamrow_s, g_o)
value_o = g_o.getresults(embeddedbeamrow_o, g_o.ResultTypes.EmbeddedBeamRow.Utot, "node")
print(value_o.index(5), value_o[5])
```

---

## OUTPUT: info

# Python wrapper commands [INFO]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## info
Displays all commands and attributes for an object.

```python
# Alternative 1
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode and defines the phases
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)

g_i.calculate()
g_i.view(phase1_s)

print(g_o.Phases.info())
```

---

## OUTPUT: linecrosssectionplot

# Python wrapper commands [LINECROSSSECTIONPLOT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## linecrosssectionplot
Creates a cross section plot defined by a line between two specified points.

```python
# Alternative 1
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode, defines the phases, and activates the line loads
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)
g_i.LineLoads.activate(phase1_s)

g_i.calculate()
g_i.view(phase1_s)
plot_o = g_o.Plots[-1]

g_o.linecrosssectionplot(plot_o, (5, 1), (10, -4))
```

---

## OUTPUT: raise

# Python wrapper commands [RAISE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## raise
Generates an error in order to test the error catching functionality.

```python
# Alternative 1
s_o, g_o = simple_test_case(s_i, g_i)

try:
    g_o.raise_()
except:
    print("Exception raised")
```

---

## OUTPUT: raiseasync

# Python wrapper commands [RAISEASYNC]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## raiseasync
Generates an error in an asynchronous thread in order to test the error catching functionality.

```python
# Alternative 1
s_o, g_o = simple_test_case(s_i, g_i)

try:
    g_o.raiseasync()
except:
    print("Exception raised")
```

---

## OUTPUT: raisethreaded

# Python wrapper commands [RAISETHREADED]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## raisethreaded
Generates an error in a synchronous thread in order to test the error catching functionality.

```python
# Alternative 1
s_o, g_o = simple_test_case(s_i, g_i)

try:
    g_o.raisethreaded()
except:
    print("Exception raised")
```

---

## OUTPUT: rename

# Python wrapper commands [RENAME]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## rename
Renames an object.

```python
# Alternative 1
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode, defines the phases, and activates the line loads
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)
g_i.LineLoads.activate(phase1_s)

g_i.calculate()
g_i.view(phase1_s)

plot_o = g_o.Plots[-1]
plot_o.rename("DeformedMesh")
```

---

## OUTPUT: reportmem

# Python wrapper commands [REPORTMEM]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## reportmem
Reports memory usage.

```python
# Alternative 1
s_o, g_o = simple_test_case(s_i, g_i)

g_o.reportmem()
```

---

## OUTPUT: set

# Python wrapper commands [SET]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## set
Sets one or more properties of one or more objects

```python
# Alternative 1
# Copies the properties of one object to another.

s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode, defines the phases, and activates the line loads
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)
g_i.LineLoads.activate(phase1_s)

g_i.calculate()
g_i.view(phase1_s)

plot1_o = g_o.Plots[-1]
plot2_o = g_o.sfplt(plot1_o)

plot2_o.set(plot1_o)
```

```python
# Alternative 2
# Changes a numerical property of an object.

plot_o = g_o.Plots[-1]
plot_o.ScaleFactor.set(50)
```

```python
# Alternative 3
# Changes a numerical property of an object.

plot1_o = g_o.Plots[-1]
plot2_o = g_o.Plots[-2]
plot1_o.ScaleFactor.set(plot2_o.ScaleFactor)
```

```python
# Alternative 4
# Changes an integer property of an object.

plot_o = g_o.Plots[-1]
plot_o.LegendSettings.Intervals.set(5)
```

```python
# Alternative 5
# Changes a text property of an object.

plot_o = g_o.Plots[-1]
plot_o.ProjectDescription.set("Excavation")
```

---

## OUTPUT: setphysicalcpucount

# Python wrapper commands [SETPHYSICALCPUCOUNT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## setphysicalcpucount
Displays or sets the amount of physical and logical CPUs.

```python
# Alternative 1
# Displays the amount of physical and logical CPUs.

s_o, g_o = simple_test_case(s_i, g_i)

g_i.gotostages()
g_i.preview(g_i.Phases[0])
print(g_o.setphysicalcpucount())
```

```python
# Alternative 2
# Sets the amount of physical and logical CPUs.

print(g_o.setphysicalcpucount(3))
```

---

## OUTPUT: setproperties

# Python wrapper commands [SETPROPERTIES]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## setproperties
Changes properties of objects.

```python
# Alternative 1
# Example 1
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode, defines the phases, and activates the line loads
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)
g_i.LineLoads.activate(phase1_s)

g_i.calculate()
g_i.view(phase1_s)

g_o.centerline((0, -10), (10, 0))
g_o.structuralforcesplot(g_o.Plots[-1])

centerline_o = g_o.CenterLines[-1]
centerline_o.setproperties("Visible", False)

# Example 2

plot_o = g_o.Plots[-1]
plot_o.setproperties("ScaleFactor", 50)
```

---

## OUTPUT: show

# Python wrapper commands [SHOW]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## show
Shows elements in a plot

```python
# Alternative 1
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode, defines the phases, and activates the line loads
g_i.gotostages()
phase1_s = g_i.phase(g_i.InitialPhase)
lineload_s = g_i.Lineloads[-1]
lineload_s.activate(phase1_s)

g_i.calculate()
g_i.view(phase1_s)

lineload_o = get_equivalent(lineload_s, g_o)
g_o.Plots[-1].hide(lineload_o)

g_o.Plots[-1].show(lineload_o)
```

---

## OUTPUT: sleep

# Python wrapper commands [SLEEP]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## sleep
Sets the number of milliseconds for computer to do nothing.

```python
# Alternative 1
s_o, g_o = simple_test_case(s_i, g_i)

g_o.sleep(2000)
```

---

## OUTPUT: slice

# Python wrapper commands [SLICE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## slice
Selects results from a list of objects with a specified criterion.

```python
# Alternative 1
# Copies full list of values from the object and creates a new object.
s_o, g_o = simple_test_case(s_i, g_i)

g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)

g_i.selectmeshpoints()
curvepoint_o = g_o.addcurvepoint("node", (8, -1))
g_o.update()
g_i.LineLoads.activate(phase1_s)

g_i.calculate()
g_i.view(phase1_s)
values_o = g_o.getresults(g_o.ResultTypes.Soil.Utot, "node", True)

slicedvalues_o = values_o.slice()
print(slicedvalues_o, values_o)
```

```python
# Alternative 2
# Selects results from a list of objects starting from a specified index.

slicedvalues_o = values_o.slice(10)
print(slicedvalues_o)
```

```python
# Alternative 3
# Selects results from a list of objects with a specific range of indicies.

slicedvalues_o = values_o.slice(1, 3)
print(slicedvalues_o)
```

---

## OUTPUT: structuralforcesplot

# Python wrapper commands [STRUCTURALFORCESPLOT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## structuralforcesplot
Creates a forces plot for structural elements.

```python
# Alternative 1
s_o, g_o = embeddedbeam_test_case(s_i, g_i)

# Changes the mode, defines the phases, adds a curvepoint and activate the line loads, embedded beams
g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)

g_i.selectmeshpoints()
curvepoint_o = g_o.addcurvepoint("node", (8, -1))
g_o.update()

g_i.LineLoads.activate(phase1_s)
g_i.EmbeddedBeamRows.activate(phase1_s)

g_i.calculate()
g_i.view(phase1_s)

embeddedbeamrow_s = g_i.EmbeddedBeamRows[-1]
embeddedbeamrow_o = get_equivalent(embeddedbeamrow_s, g_o)

plot_o = g_o.structureplot(embeddedbeamrow_o)
g_o.structuralforcesplot(plot_o)
```

---

## OUTPUT: structureplot

# Python wrapper commands [STRUCTUREPLOT]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## structureplot
Creates a plot for structural elements.

```python
# Alternative 1
s_o, g_o = embeddedbeam_test_case(s_i, g_i)

# Changes the mode, defines the phases, adds a curvepoint and activates the line loads, embedded beams
g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)

g_i.selectmeshpoints()
curvepoint_o = g_o.addcurvepoint("node", (8, -1))
g_o.update()

g_i.LineLoads.activate(phase1_s)
g_i.EmbeddedBeamRows.activate(phase1_s)

g_i.calculate()
g_i.view(phase1_s)

embeddedbeamrow_s = g_i.EmbeddedBeamRows[-1]
embeddedbeamrow_o = get_equivalent(embeddedbeamrow_s, g_o)

g_o.structureplot(embeddedbeamrow_o)
```

---

## OUTPUT: tabulate

# Python wrapper commands [TABULATE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## tabulate
Displays a table with specified objects and their properties.

```python
# Alternative 1
# Displays a table with specified objects and their properties.

# Example 1
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode, defines the phases, adds curvepoints and activates the line loads
g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)

g_i.selectmeshpoints()
curvepoint1_o = g_o.addcurvepoint("node", (8, -1))
curvepoint2_o = g_o.addcurvepoint("node", (8, -3))
g_o.update()
g_i.LineLoads.activate(phase1_s)

g_i.calculate()
g_i.view(phase1_s)

plots_o = g_o.Plots
print(g_o.tabulate(plots_o))

# Example 2
g_o.centerline((0, -10), (12, 0))
g_o.centerline((0, -4), (12, -4))

centerlines_o = g_o.CenterLines
print(g_o.tabulate(centerlines_o))

# Example 3

curvepoints_o = g_o.CurvePoints.Nodes
print(g_o.tabulate(curvepoints_o))
```

```python
# Alternative 2
# Displays a table with specified objects and some of their properties.

# Example 1
s_o, g_o = embeddedbeam_test_case(s_i, g_i)

# Changes the mode, defines the phases, adds curvepoints and activates the line loads, embedded beams
g_i.gotostages()
phase0_s = g_i.InitialPhase
phase1_s = g_i.phase(phase0_s)

g_i.selectmeshpoints()
curvepoint_o = g_o.addcurvepoint("node", (8, -1))
g_o.addcurvepoint("stresspoint", (5, 0))
g_o.addcurvepoint("stresspoint", (7, -3))
g_o.update()

g_i.LineLoads.activate(phase1_s)
g_i.EmbeddedBeamRows.activate(phase1_s)

g_i.calculate()
g_i.view(phase1_s)

embeddedbeamrow_s = g_i.EmbeddedBeamRows[-1]
embeddedbeamrow_o = get_equivalent(embeddedbeamrow_s, g_o)

g_o.structureplot(embeddedbeamrow_o)

plots_o = g_o.Plots
print(g_o.tabulate(plots_o, "ResultType"))

# Example 2
g_o.centerline((0, -10), (12, 0))

material_i = g_i.Materials[-2]

centerlinecriteriaobject = g_o.centerlineconfig(material_i)
centerlinecriteriaobject.xmin_symmetry = False
centerlinecriteriaobject.xmax_symmetry = False
centerlinecriteriaobject.ymin_symmetry = False
centerlinecriteriaobject.ymax_symmetry = False

g_o.add(g_o.Plots[-1], centerlinecriteriaobject)
g_o.generate(phase1_s, centerlinecriteriaobject)

centerlines_o = g_o.CenterLines
print(g_o.tabulate(centerlines_o, "CenterLineType"))

# Example 3
curvepoints_o = g_o.CurvePoints.StressPoints
print(g_o.tabulate(curvepoints_o, "x y"))
```

```python
# Alternative 3
# Displays a table with specified objects that fulfill a specified condition, and some of their properties.

# Example 1
g_o.Plots[-1].ScaleFactor = 50
print(g_o.tabulate(plots_o, "ResultType", "ScaleFactor=50"))

# Example 2
print(g_o.tabulate(curvepoints_o, "x y", "y<-1"))
```

```python
# Alternative 4
# Displays a table with specified objects.

g_o.centerline((0, -5), (10, 0))
centerline_o = g_o.CenterLines[-1]
print(g_o.tabulate(centerline_o.Points))
```

```python
# Alternative 5
# Displays a table with specified objects and some of their properties.

centerline_o = g_o.CenterLines[-1]
print(g_o.tabulate(centerline_o.Points, "x y"))
```

```python
# Alternative 6
# Displays a table with specified objects that fulfill a specified condition, and some of their properties.

centerline_o = g_o.CenterLines[-1]
print(g_o.tabulate(centerline_o.Points, "x y", "x>2"))
```

---

## OUTPUT: testasync

# Python wrapper commands [TESTASYNC]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## testasync
Tests that asynchronous task execution works correctly.

```python
# Alternative 1
s_o, g_o = simple_test_case(s_i, g_i)

g_o.testasync(30)
```

---

## OUTPUT: update

# Python wrapper commands [UPDATE]
The remote scripting server in PLAXIS 2D Input should be activated before starting the session. This notebook has two available objects, the "s_i" object which represents the application server and the "g_i" object which represents the global environment for the PLAXIS 2D Input application. In these examples, the PLAXIS 2D Output application will be opened from Input and connecting to the remote scripting server for Output will provide us with two additional objects, "s_o" and "g_o". The input commands can be accessed from the "g_i" object and similarly, the output commands can be accessed from the "g_o" object.

```python
from plxscripting.easy import *

def create_geometry(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create a soil layer, assign a test material to soil, create a line load
    with dynamic multiplier
    """
    s_i.new()
    g_i.borehole(0)
    g_i.soillayer(5)
    material = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, 
                           "gammaUnsat", 17, "gammaSat", 20, "Gref", 2000)
    g_i.Soils[0].Material = material
    g_i.gotostructures()
    g_i.lineload((4, 0), (9, 0))
    lineload_g = g_i.LineLoads[-1]
    loadmultiplier_g = g_i.loadmultiplier()
    loadmultiplier_g.setproperties("Amplitude", 5, "Frequency", 2)

    
    lineload_g.LineLoad.qy_start = -100
    lineload_g.LineLoad.Multipliery = loadmultiplier_g


def simple_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    
    """
    create_geometry(s_i, g_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def dynamic_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, generate the mesh and add a 
    dynamic calculation phase
    """
    create_geometry(s_i, g_i)

    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    g_i.gotostages()
    phase1_s = g_i.phase(g_i.InitialPhase)
    phase1_s.DeformCalcType = phase1_s.DeformCalcType.dynamic
    phase1_s.Deform.TimeIntervalSeconds = 2
    phase1_s.MaxStepsStored = 5 
    
    return s, g
```

```python
def embeddedbeam_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features and generate the mesh
    """
    create_geometry(s_i, g_i)
    
    material_i = g_i.embeddedbeammat("E", 1, "w", 1, "A", 1)
    g_i.embeddedbeamrow((4, -1), (9, -1), "Material", material_i)
    
    g_i.gotomesh()
    g_i.mesh(0.1)
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g


def suction_test_case(s_i, g_i):
    """
    Takes the plaxis variables s_i, g_i and performs a series of operations
    to create geometry features, add groundwater flow boundary conditions, 
    generate the mesh and set the boundary conditions
    """
    s_i.new()

    g_i.SoilContour.initializerectangular(0, 0, 10, 1)
    borehole_g = g_i.borehole(0)
    g_i.soillayer(0)
    g_i.setsoillayerlevel(borehole_g, 0, 3)
    material_i = g_i.soilmat("MaterialName", "Test", "SoilModel", 1, "DrainageType", 1, 
                             "Gref", 500, "gammaSat", 10, "gammaUnsat", 10, "perm_primary_horizontal_axis", 
                             0.1, "perm_vertical_axis", 0.5)

    g_i.Soils[0].Material = material_i
    
    g_i.gotostructures()
    g_i.lineload((3, 3), (7, 3))
    
    g_i.gotomesh()
    g_i.mesh(0.05)
    
    g_i.gotowater()
    phase0_s = g_i.InitialPhase
    
    g_i.set((g_i.GroundwaterFlow.BoundaryXMin, g_i.GroundwaterFlow.BoundaryXMax), phase0_s, "Closed")
    
    gwflowbasebc1_s = g_i.GWFlowBaseBC[-3]
    gwflowbasebc2_s = g_i.GWFlowBaseBC[0]
    
    gwflowbasebc1_s.Behaviour.set(phase0_s, "Head") 
    gwflowbasebc1_s.Href.set(phase0_s, 1)
    gwflowbasebc2_s.Behaviour.set(phase0_s, "Head")
    gwflowbasebc2_s.Href.set(phase0_s, 2)

    gwflowbasebc1_s.activate(phase0_s)
    gwflowbasebc2_s.activate(phase0_s)
    

    g_i.gotostages()
    phase0_s.DeformCalcType = "Flow Only"
    
    output_port = g_i.viewmesh()
    s, g = new_server('localhost', port=output_port, password=s_i.connection._password)
    
    return s, g
```

## update
Saves the selected curve points and closes output.

```python
# Alternative 1
s_o, g_o = simple_test_case(s_i, g_i)

# Changes the mode and adds a curvepoint
g_i.gotostages()

g_i.selectmeshpoints()
curvepoint_o = g_o.addcurvepoint("node", (8, -1))

g_o.update()
```

---
