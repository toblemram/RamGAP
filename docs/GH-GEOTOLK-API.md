# RamGAP — Grasshopper GeoTolk-komponent

Hent tolkede borringer (SND-filer) fra RamGAP og bruk lagdelingen direkte i Grasshopper.

---

## Oversikt

Når SND-filer er tolket i RamGAP GeoTolk, lagres lagdelingen (jordtype + dybdeintervall) i databasen. Med denne Grasshopper-komponenten kan du hente **alle** tolkede borringer i et prosjekt med ett kall — klar til bruk som geometri i GH.

**Inndata (GH-komponent):**
| Parameter | Type | Beskrivelse |
|-----------|------|-------------|
| `BaseURL` | string | Server-URL, f.eks. `http://localhost:5050` |
| `ProjectName` | string | Prosjektnavn i RamGAP |
| `Username` | string | Brukernavn (filtrerer på tolk) |
| `Radius` | double | Visningsradius for sylinderne (m) |
| `Run` | bool | Sett til true for å kjøre |

**Utdata (GH-komponent):**
| Parameter | Type | Beskrivelse |
|-----------|------|-------------|
| `Filenames` | list\<string\> | Filnavn per borrhull |
| `Positions` | list\<Point3d\> | Borrhullsposisjon (X=easting, Y=northing, Z=terreng) |
| `LayerTypes` | DataTree\<string\> | Jordtype per lag (`leire`, `sand`, `fjell`, …) |
| `LayerDepths` | DataTree\<Interval\> | Dybdeintervall per lag (start → end) |
| `MaxDepths` | list\<double\> | Maks dybde per borrhull |
| `Geometry` | DataTree\<Brep\> | 3D-sylindere per lag (posisjonert på X,Y,Z fra SND) |
| `Colors` | DataTree\<Color\> | Farge per lag-sylinder |

---

## Base URL

```
http://localhost:5050        ← lokal utvikling
https://din-server.no:5050   ← produksjon
```

---

## API-endepunkt

### Hent alle tolkede borringer i et prosjekt

```
GET /api/geotolk/gh/boreholes?project_name={navn}&username={brukernavn}
```

| Parameter | Type | Påkrevd | Beskrivelse |
|-----------|------|---------|-------------|
| `project_name` | string | **Ja** | Prosjektnavn (eksakt match) |
| `username` | string | Nei | Filtrer på tolk-brukernavn — filtrerer også prosjekttilgang |

**Response:**
```json
{
  "success": true,
  "project_id": 5,
  "count": 2,
  "boreholes": [
    {
      "id": 14,
      "filename": "BH-01.SND",
      "max_depth": 32.5,
      "num_layers": 4,
      "x": 128655.85,
      "y": 1016459.72,
      "z": 6.66,
      "layers": [
        { "type": "sand",  "start": 0.0,  "end": 5.2 },
        { "type": "leire", "start": 5.2,  "end": 18.0 },
        { "type": "sand",  "start": 18.0, "end": 27.5 },
        { "type": "fjell", "start": 27.5, "end": 32.5 }
      ],
      "sounding": {
        "depth": [0.0, 0.02, 0.04],
        "c2": [0.5, 0.6, 0.7],
        "c3": [null, null, null],
        "c4": [null, null, null]
      },
      "events": {
        "spyling": [[12.0, 14.5]],
        "slag": []
      }
    },
    {
      "id": 15,
      "filename": "BH-02.SND",
      "max_depth": 28.0,
      "num_layers": 3,
      "layers": [ ... ],
      "sounding": { ... },
      "events": { ... }
    }
  ]
}
```

Du kan også bruke `project_id` istedenfor `project_name`:
```
GET /api/geotolk/gh/boreholes?project_id=5
```

---

## Grasshopper-komponent — C# (GH_Component)

### RegisterInputParams / RegisterOutputParams

```csharp
protected override void RegisterInputParams(GH_InputParamManager pManager)
{
    pManager.AddTextParameter("BaseURL", "URL", "RamGAP backend base URL",
        GH_ParamAccess.item, "http://localhost:5050");
    pManager.AddTextParameter("ProjectName", "Prj", "Prosjektnavn i RamGAP",
        GH_ParamAccess.item);
    pManager.AddTextParameter("Username", "Usr", "Brukernavn (filtrerer på tolk)",
        GH_ParamAccess.item);
    pManager[2].Optional = true;
    pManager.AddNumberParameter("Radius", "R", "Visningsradius for sylinderne (m)",
        GH_ParamAccess.item, 0.5);
    pManager.AddBooleanParameter("Run", "Run", "Sett til true for å kjøre",
        GH_ParamAccess.item, false);
}

protected override void RegisterOutputParams(GH_OutputParamManager pManager)
{
    pManager.AddTextParameter("Filenames", "F", "Filnavn per borrhull",
        GH_ParamAccess.list);
    pManager.AddPointParameter("Positions", "Pts", "Borrhullsposisjon (X,Y,Z fra SND)",
        GH_ParamAccess.list);
    pManager.AddTextParameter("LayerTypes", "LT", "Jordtype per lag",
        GH_ParamAccess.tree);
    pManager.AddIntervalParameter("LayerDepths", "LD", "Dybdeintervall per lag",
        GH_ParamAccess.tree);
    pManager.AddNumberParameter("MaxDepths", "MD", "Maks dybde per borrhull",
        GH_ParamAccess.list);
    pManager.AddBrepParameter("Geometry", "G", "3D-sylindere per lag",
        GH_ParamAccess.tree);
    pManager.AddColourParameter("Colors", "C", "Farge per lag-sylinder",
        GH_ParamAccess.tree);
}
```

### SolveInstance

```csharp
protected override void SolveInstance(IGH_DataAccess DA)
{
    string baseUrl = "", projectName = "", username = "";
    double radius = 0.5;
    bool run = false;

    DA.GetData(0, ref baseUrl);
    DA.GetData(1, ref projectName);
    DA.GetData(2, ref username);
    DA.GetData(3, ref radius);
    DA.GetData(4, ref run);

    if (!run || string.IsNullOrEmpty(projectName)) return;

    // --- 1) Bygg URL ---
    var url = $"{baseUrl.TrimEnd('/')}/api/geotolk/gh/boreholes?project_name={Uri.EscapeDataString(projectName)}";
    if (!string.IsNullOrEmpty(username))
        url += $"&username={Uri.EscapeDataString(username)}";

    // --- 2) HTTP GET ---
    string json;
    var request = System.Net.WebRequest.Create(url);
    using (var response = request.GetResponse())
    using (var reader = new System.IO.StreamReader(response.GetResponseStream()))
        json = reader.ReadToEnd();

    var root = Newtonsoft.Json.Linq.JObject.Parse(json);
    if (root["success"]?.Value<bool>() != true)
    {
        AddRuntimeMessage(GH_RuntimeMessageLevel.Error,
            root["error"]?.ToString() ?? "Unknown API error");
        return;
    }

    var bhs = root["boreholes"] as Newtonsoft.Json.Linq.JArray;
    if (bhs == null || bhs.Count == 0)
    {
        AddRuntimeMessage(GH_RuntimeMessageLevel.Warning,
            "Ingen tolkede borringer funnet i dette prosjektet.");
        return;
    }

    // --- 3) Parse data → output ---
    var filenames  = new List<string>();
    var positions  = new List<Point3d>();
    var maxDepths  = new List<double>();
    var typeTree   = new DataTree<string>();
    var depthTree  = new DataTree<Grasshopper.Kernel.Types.GH_Interval>();
    var geomTree   = new DataTree<Grasshopper.Kernel.Types.GH_Brep>();
    var colorTree  = new DataTree<System.Drawing.Color>();

    for (int i = 0; i < bhs.Count; i++)
    {
        var path = new GH_Path(i);
        var bh   = bhs[i];

        filenames.Add(bh["filename"].ToString());
        maxDepths.Add(bh["max_depth"]?.Value<double>() ?? 0);

        // Koordinater fra SND-header (X=easting, Y=northing, Z=terreng)
        double px = bh["x"]?.Value<double>() ?? 0;
        double py = bh["y"]?.Value<double>() ?? 0;
        double pz = bh["z"]?.Value<double>() ?? 0;
        positions.Add(new Point3d(px, py, pz));

        var layers = bh["layers"] as Newtonsoft.Json.Linq.JArray;
        if (layers == null) continue;

        foreach (var layer in layers)
        {
            string soilType = layer["type"].ToString();
            double start    = layer["start"].Value<double>();
            double end      = layer["end"].Value<double>();

            typeTree.Add(soilType, path);
            depthTree.Add(
                new Grasshopper.Kernel.Types.GH_Interval(new Interval(start, end)),
                path);

            // Farge
            colorTree.Add(SoilColor(soilType), path);

            // 3D-sylinder posisjonert på borrhullets X,Y,Z
            double topZ = pz - start;
            double botZ = pz - end;
            double h    = topZ - botZ;
            if (h < 0.001) continue;

            var plane = new Plane(new Point3d(px, py, botZ), Vector3d.ZAxis);
            var cyl   = new Cylinder(new Circle(plane, radius), h);
            var brep  = cyl.ToBrep(true, true);
            if (brep != null)
                geomTree.Add(new Grasshopper.Kernel.Types.GH_Brep(brep), path);
        }
    }

    DA.SetDataList(0, filenames);
    DA.SetDataList(1, positions);
    DA.SetDataTree(2, typeTree);
    DA.SetDataTree(3, depthTree);
    DA.SetDataList(4, maxDepths);
    DA.SetDataTree(5, geomTree);
    DA.SetDataTree(6, colorTree);
}
```

### SoilColor-hjelpemetode

```csharp
private static System.Drawing.Color SoilColor(string soilType)
{
    switch (soilType.ToLowerInvariant())
    {
        case "leire":      return System.Drawing.Color.FromArgb(139, 90, 43);
        case "sand":       return System.Drawing.Color.FromArgb(218, 189, 90);
        case "silt":       return System.Drawing.Color.FromArgb(194, 170, 120);
        case "morene":     return System.Drawing.Color.FromArgb(150, 150, 150);
        case "fjell":      return System.Drawing.Color.FromArgb(100, 100, 100);
        case "grus":       return System.Drawing.Color.FromArgb(200, 150, 80);
        case "torv":       return System.Drawing.Color.FromArgb(80, 50, 20);
        case "fylling":    return System.Drawing.Color.FromArgb(150, 100, 160);
        case "kvikkleire": return System.Drawing.Color.FromArgb(200, 60, 60);
        default:           return System.Drawing.Color.FromArgb(220, 220, 220);
    }
}
```

---

## Alternativ: GHPython-komponent

For de som foretrekker Python i Grasshopper:

### Inndata/Utdata

**Inndata (høyreklikk → Manage Input Parameters):**
- `base_url` (string) — `http://localhost:5050`
- `project_name` (string) — Prosjektnavn
- `username` (string, optional) — Brukernavn
- `radius` (float) — Visningsradius
- `run` (bool) — Toggle

**Utdata (høyreklikk → Manage Output Parameters):**
- `filenames`, `positions`, `layer_types`, `layer_depths`, `max_depths`, `geometry`, `colors`

### GHPython-kode

```python
"""RamGAP GeoTolk — Hent alle borringer med lagdeling"""
import urllib2
import urllib
import json
import Rhino.Geometry as rg
import System.Drawing as sd
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path

COLOR_MAP = {
    "leire":      sd.Color.FromArgb(139, 90, 43),
    "sand":       sd.Color.FromArgb(218, 189, 90),
    "silt":       sd.Color.FromArgb(194, 170, 120),
    "morene":     sd.Color.FromArgb(150, 150, 150),
    "fjell":      sd.Color.FromArgb(100, 100, 100),
    "grus":       sd.Color.FromArgb(200, 150, 80),
    "torv":       sd.Color.FromArgb(80, 50, 20),
    "fylling":    sd.Color.FromArgb(150, 100, 160),
    "kvikkleire": sd.Color.FromArgb(200, 60, 60),
    "annet":      sd.Color.FromArgb(220, 220, 220),
}

filenames    = []
positions    = []
layer_types  = DataTree[str]()
layer_depths = DataTree[object]()
max_depths   = []
geometry     = DataTree[rg.Brep]()
colors       = DataTree[sd.Color]()

if run and project_name:
    url = "{}/api/geotolk/gh/boreholes?project_name={}".format(
        base_url.rstrip("/"), urllib.quote(project_name))
    if username:
        url += "&username={}".format(urllib.quote(username))

    resp = urllib2.urlopen(urllib2.Request(url))
    data = json.loads(resp.read())

    if data.get("success"):
        for i, bh in enumerate(data["boreholes"]):
            path = GH_Path(i)
            filenames.append(bh["filename"])
            max_depths.append(bh["max_depth"])

            # Koordinater fra SND-header
            px = bh.get("x") or 0
            py = bh.get("y") or 0
            pz = bh.get("z") or 0
            positions.append(rg.Point3d(px, py, pz))

            for layer in bh["layers"]:
                soil = layer["type"]
                start = layer["start"]
                end   = layer["end"]

                layer_types.Add(soil, path)
                layer_depths.Add(rg.Interval(start, end), path)
                colors.Add(COLOR_MAP.get(soil, COLOR_MAP["annet"]), path)

                # 3D-sylinder posisjonert på borrhullets X,Y,Z
                top_z = pz - start
                bot_z = pz - end
                h = top_z - bot_z
                if h > 0.001:
                    plane = rg.Plane(rg.Point3d(px, py, bot_z), rg.Vector3d.ZAxis)
                    cyl = rg.Cylinder(rg.Circle(plane, radius), h)
                    brep = cyl.ToBrep(True, True)
                    if brep:
                        geometry.Add(brep, path)
```

---

## Farger per jordtype

| Jordtype | Farge | RGB |
|----------|-------|-----|
| `leire` | Brun | (139, 90, 43) |
| `sand` | Gul | (218, 189, 90) |
| `silt` | Lys brun | (194, 170, 120) |
| `morene` | Grå | (150, 150, 150) |
| `fjell` | Mørk grå | (100, 100, 100) |
| `grus` | Orange | (200, 150, 80) |
| `torv` | Mørk brun | (80, 50, 20) |
| `fylling` | Lilla | (150, 100, 160) |
| `kvikkleire` | Rød | (200, 60, 60) |
| `annet` | Hvit | (220, 220, 220) |

---

## Komplett arbeidsflyt i Grasshopper

```
┌──────────────────────┐
│  Panel: BaseUrl      │─── "http://localhost:5050"
└────────┬─────────────┘
         │
┌────────┴──────────────┐  ┌──────────────────┐  ┌────────────┐
│ Panel: ProjectName    │  │ Panel: Username   │  │ Slider: R  │
│ "Støttemur E18"       │  │ "TBLM"            │  │ 0.5        │
└────────┬──────────────┘  └───────┬───────────┘  └──────┬─────┘
         │                         │                     │
    ┌────┴─────────────────────────┴─────────────────────┴────┐
    │  GH-komponent: RamGAP GeoTolk                           │
    │  [URL] [Prj] [Usr] [R] [Run]                            │
    └──┬──────┬───────────┬────────────┬──────────┬───────────┘
       │      │           │            │          │
   Filenames LayerTypes LayerDepths  Geometry   Colors
       │      │           │            │          │
       │      │           │       ┌────┴──────────┴───┐
       │      │           │       │  Custom Preview    │
       │      │           │       └────────────────────┘
       ▼      ▼           ▼
   (Panel) (Panel)    (Panel)
```

---

## Feilsøking

| Problem | Løsning |
|---------|---------|
| `urllib2` mangler | Sjekk at GHPython bruker IronPython (standard i Rhino 7/8) |
| Timeout / connection refused | Start RamGAP backend: `python backend/app.py` |
| Ingen borringer i output | Tolk SND-filer i RamGAP frontend først |
| "Project not found" | Sjekk at prosjektnavnet er identisk med det i RamGAP |
| 404 på endepunkt | Oppdater RamGAP backend til nyeste versjon |
| Sylinderne er på feil sted | Bruk en Move-komponent med borrhullsposisjon (x,y,z) |
