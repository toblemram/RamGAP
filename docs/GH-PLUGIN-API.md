# RamGAP — Grasshopper Plugin API

Dette dokumentet beskriver hvordan en Grasshopper-plugin skal kommunisere med RamGAP-backend for å:

1. Koble til et prosjekt
2. Opprette eller velge en modeling-aktivitet
3. Laste opp Excel-inputfil
4. Sende optimeringsresultater (run-report.json, run-summary.md, IFC)
5. Hente resultater og nedlastingslenker

---

## Base URL

```
http://localhost:5050        ← lokal utvikling
https://din-server.no:5050   ← produksjon (sett i konfig)
```

Konfigurer base URL som en parameter i GH-komponenten.

---

## Autentisering

Ingen token-autentisering nå. Brukernavn sendes som JSON-felt eller query-parameter.
Bruk Windows-brukernavn (`Environment.UserName` i C#).

---

## Aktivitetsstatus — livssyklus

En `ModelingActivity` går gjennom disse statusene:

| Status | Betyr |
|--------|-------|
| `active` | Opprettet, ingen filer lastet opp enda |
| `has_excel` | Excel-inputfil er lastet opp |
| `has_results` | GH-optimeringsresultater er mottatt |

---

## Lagringsstruktur i Azure Blob Storage

Filer lagres med følgende navnekonvensjon:

```
projects/{project_id}/modeling/{activity_id}/excel/{filename}
projects/{project_id}/modeling/{activity_id}/ifc/{filename}
```

`run-report.json` og `run-summary.md` lagres direkte i databasen (ikke Blob Storage).

---

## Arbeidsflyt — steg for steg

```
[GH Plugin]
    │
    ├─ 1. List prosjekter          GET  /api/projects?username=TBLM
    │
    ├─ 2a. Velg eksisterende       (bruker velger fra liste)
    │   eller
    ├─ 2b. Opprett nytt prosjekt   POST /api/projects
    │
    ├─ 3. List aktiviteter         GET  /api/modeling/activities?project_id=5
    │
    ├─ 4a. Velg eksisterende       (bruker velger fra liste)
    │   eller
    ├─ 4b. Opprett ny aktivitet    POST /api/modeling/activities
    │
    ├─ 5. Last opp Excel           POST /api/modeling/activities/{id}/upload/excel
    │
    ├─ 6. Send GH-resultater       POST /api/modeling/activities/{id}/upload/results
    │
    └─ 7. Hent resultater (valgfritt)  GET /api/modeling/activities/{id}/results
```

---

## Endepunkter

### 1. List prosjekter

```
GET /api/projects?username={brukernavn}
```

**Response:**
```json
{
  "count": 2,
  "projects": [
    {
      "id": 5,
      "name": "Støttemur E18",
      "description": "...",
      "created_by": "TBLM",
      "is_active": true,
      "allowed_users": ["kollega1"],
      "created_at": "2026-03-23T08:00:00",
      "updated_at": "2026-03-23T08:00:00"
    }
  ]
}
```

---

### 2. Opprett prosjekt (valgfritt)

```
POST /api/projects
Content-Type: application/json
```

**Body:**
```json
{
  "name": "Støttemur E18",
  "description": "Optimalisering av støttemur langs E18",
  "created_by": "TBLM",
  "allowed_users": ["kollega1"]
}
```

**Response `201`:**
```json
{
  "project": {
    "id": 5,
    "name": "Støttemur E18",
    "description": "...",
    "created_by": "TBLM",
    "is_active": true,
    "allowed_users": [],
    "created_at": "2026-03-23T08:00:00",
    "updated_at": "2026-03-23T08:00:00"
  }
}
```

---

### 3. List modeling-aktiviteter

```
GET /api/modeling/activities?project_id={prosjekt_id}
GET /api/modeling/activities?username={brukernavn}
```

> `project_id` har prioritet over `username` hvis begge sendes.

**Response:**
```json
{
  "activities": [
    {
      "id": 12,
      "project_id": 5,
      "name": "Kjøring 1 — 69 seks.",
      "username": "TBLM",
      "status": "has_results",
      "has_excel": true,
      "has_ifc": true,
      "has_results": true,
      "excel_filename": "input_mur.xlsx",
      "ifc_filename": "retaining_wall.ifc",
      "created_at": "2026-03-23T08:00:00",
      "updated_at": "2026-03-23T08:05:00"
    }
  ]
}
```

---

### 4. Opprett modeling-aktivitet

```
POST /api/modeling/activities
Content-Type: application/json
```

**Body:**

| Felt | Type | Påkrevd | Beskrivelse |
|------|------|---------|-------------|
| `name` | string | **Ja** | Navn på kjøringen, f.eks. `"Kjøring 2 — oppdatert last"` |
| `username` | string | **Ja** | Windows-brukernavn |
| `project_id` | int | Nei | Kobler aktiviteten til et prosjekt |

```json
{
  "project_id": 5,
  "name": "Kjøring 2 — oppdatert last",
  "username": "TBLM"
}
```

**Response `201`:**
```json
{
  "activity": {
    "id": 13,
    "project_id": 5,
    "name": "Kjøring 2 — oppdatert last",
    "username": "TBLM",
    "status": "active",
    "has_excel": false,
    "has_ifc": false,
    "has_results": false,
    "excel_filename": null,
    "ifc_filename": null,
    "created_at": "2026-03-23T08:00:00",
    "updated_at": "2026-03-23T08:00:00"
  }
}
```

Lagre `activity.id` — brukes i alle påfølgende kall.

---

### 5. Hent én aktivitet

```
GET /api/modeling/activities/{activity_id}
```

**Response:**
```json
{
  "activity": { ... }
}
```

---

### 6. Slett aktivitet

```
DELETE /api/modeling/activities/{activity_id}
```

**Response:**
```json
{ "success": true }
```

---

### 7. Last opp Excel-fil

```
POST /api/modeling/activities/{activity_id}/upload/excel
Content-Type: multipart/form-data
```

**Form-felt:**
| Felt | Type | Beskrivelse |
|------|------|-------------|
| `file` | fil | Excel-filen (.xlsx) |

Filen lagres til Azure Blob Storage under:
`projects/{project_id}/modeling/{activity_id}/excel/{filename}`

**Response:**
```json
{
  "success": true,
  "blob_name": "projects/5/modeling/13/excel/input_mur.xlsx",
  "activity": {
    "id": 13,
    "status": "has_excel",
    "has_excel": true,
    "excel_filename": "input_mur.xlsx",
    ...
  }
}
```

---

### 8. Send GH-optimeringsresultater

```
POST /api/modeling/activities/{activity_id}/upload/results
Content-Type: multipart/form-data
```

**Form-felt:**
| Felt | Type | Påkrevd | Beskrivelse |
|------|------|---------|-------------|
| `report` | fil | **Ja** | `run-report.json` — full JSON fra optimeringen |
| `summary` | fil | Nei | `run-summary.md` — markdown-sammendrag |
| `ifc` | fil | Nei | IFC-geometrifil fra GH |

> `run-report.json` og `run-summary.md` lagres i databasen (ikke Blob Storage).
> IFC-filen lastes opp til Blob Storage under `projects/{project_id}/modeling/{activity_id}/ifc/{filename}`.

**report (run-report.json) — faktisk format fra GH:**
```json
{
  "ProjectName": "RetainingWall",
  "RunId": "b476858ffb864426a1d228bfc395d17d",
  "CreatedUtc": "2026-03-23T07:50:56.3059713+00:00",
  "Config": {
    "SegmentLength": 1.0,
    "EmbedmentDepth": 0.5,
    "HeightOffset": 0.0,
    "GammaWall": 23.0,
    "GammaBackfill": 19.0,
    "GammaBase": 19.0,
    "PhiBackfillDeg": 42.0,
    "PhiBaseDeg": 37.0,
    "AdhesionBase": 9.0,
    "SurchargeQk": 5.0,
    "BogieLoad": 16.75,
    "LoadFactorUniform": 1.3,
    "LoadFactorBogie": 1.15,
    "HorizontalTopLoad": 2.0,
    "VerticalTopLoad": 0.0,
    "SlidingMin": 1.5,
    "OverturningMin": 2.0,
    "BearingMin": 3.0,
    "TopWidthMin": 0.6,
    "TopWidthMax": 3.0,
    "TopWidthStep": 0.1,
    "BottomWidthMin": 1.2,
    "BottomWidthMax": 5.0,
    "BottomWidthStep": 0.1,
    "AngleMinDeg": 0.0,
    "AngleMaxDeg": 15.0,
    "AngleStepDeg": 1.0,
    "WallThicknessZ": 1.0,
    "SmoothWindow": 1,
    "ProjectName": "RetainingWall",
    "RunId": "b476858ffb864426a1d228bfc395d17d"
  },
  "Sections": [
    {
      "Index": 0,
      "Station": 0.0,
      "Height": 21.25,
      "TopWidth": 3.0,
      "BottomWidth": 5.0,
      "FaceAngleDeg": 15.0,
      "Area": 0.0,
      "VolumePerMeter": 1.7976931348623157E+308,
      "SmoothedTopWidth": 3.0,
      "SmoothedBottomWidth": 5.0,
      "SmoothedFaceAngleDeg": 15.0,
      "Checks": {
        "SlidingFactor": 1.72,
        "OverturningFactor": 2.45,
        "BearingFactor": 3.10,
        "SlidingOk": true,
        "OverturningOk": true,
        "BearingOk": true,
        "AllOk": true,
        "GoverningCheck": "Sliding"
      },
      "Diagnostics": {}
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "activity": {
    "id": 13,
    "status": "has_results",
    "has_excel": true,
    "has_ifc": true,
    "ifc_filename": "model.ifc",
    ...
  }
}
```

---

### 9. Hent resultater (for frontend/visning)

```
GET /api/modeling/activities/{activity_id}/results
```

Returnerer den lagrede `run-report.json` og `run-summary.md` direkte fra databasen.

**Response:**
```json
{
  "run_report": { ... },
  "run_summary": "## Sammendrag\n...",
  "activity": { "id": 13, "status": "has_results", ... }
}
```

Returnerer `404` hvis ingen resultater er lastet opp enda.

---

## Eksempel — C# med HttpClient

```csharp
using System.Net.Http;
using System.Net.Http.Json;
using System.Net.Http.Headers;

var baseUrl  = "http://localhost:5050";
var client   = new HttpClient();
var username = Environment.UserName;  // f.eks. "TBLM"

// --- 1. List prosjekter ---
var projects = await client.GetFromJsonAsync<ProjectsResponse>(
    $"{baseUrl}/api/projects?username={username}"
);
// projects.projects[i].id  ← bruk dette som project_id

// --- 2. Opprett aktivitet ---
var actResp = await client.PostAsJsonAsync(
    $"{baseUrl}/api/modeling/activities",
    new { project_id = 5, name = "GH Run 1", username }
);
var act = (await actResp.Content.ReadFromJsonAsync<ActivityResponse>())!.activity;
int activityId = act.id;

// --- 3. Last opp Excel ---
using var excelContent = new MultipartFormDataContent();
excelContent.Add(
    new ByteArrayContent(File.ReadAllBytes("input.xlsx")) {
        Headers = { ContentType = new MediaTypeHeaderValue(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet") }
    }, "file", "input.xlsx"  // ← form-felt må hete "file"
);
await client.PostAsync(
    $"{baseUrl}/api/modeling/activities/{activityId}/upload/excel",
    excelContent
);

// --- 4. Send resultater ---
using var resultsContent = new MultipartFormDataContent();
resultsContent.Add(
    new ByteArrayContent(File.ReadAllBytes("run-report.json")) {
        Headers = { ContentType = new MediaTypeHeaderValue("application/json") }
    }, "report", "run-report.json"   // ← form-felt må hete "report"
);
resultsContent.Add(
    new ByteArrayContent(File.ReadAllBytes("run-summary.md")) {
        Headers = { ContentType = new MediaTypeHeaderValue("text/markdown") }
    }, "summary", "run-summary.md"   // ← valgfritt, form-felt heter "summary"
);
// IFC er valgfritt:
resultsContent.Add(
    new ByteArrayContent(File.ReadAllBytes("model.ifc")) {
        Headers = { ContentType = new MediaTypeHeaderValue("application/octet-stream") }
    }, "ifc", "model.ifc"            // ← valgfritt, form-felt heter "ifc"
);
var finalResp = await client.PostAsync(
    $"{baseUrl}/api/modeling/activities/{activityId}/upload/results",
    resultsContent
);
Console.WriteLine(await finalResp.Content.ReadAsStringAsync());
```

### Hjelpeklasser for deserialisering

```csharp
record ProjectsResponse(List<ProjectDto> projects, int count);
record ProjectDto(int id, string name, string description, string created_by);

record ActivityResponse(ActivityDto activity);
record ActivityDto(
    int id, int? project_id, string name, string username,
    string status, bool has_excel, bool has_ifc, bool has_results,
    string? excel_filename, string? ifc_filename
);
```

---

## Nedlastings-URLer (for frontend)

Disse returnerer en tidsavgrenset SAS-URL til Azure Blob Storage (gyldig i **1 time**):

```
GET /api/modeling/activities/{id}/download/excel
GET /api/modeling/activities/{id}/download/ifc
```

**Response:**
```json
{
  "url": "https://<storage>.blob.core.windows.net/project-files/projects/5/modeling/13/excel/input.xlsx?sv=...",
  "filename": "input_mur.xlsx"
}
```

Returnerer `404` hvis ingen fil er lastet opp for den typen.

---

## Feilhåndtering

| HTTP-kode | Betydning |
|-----------|-----------|
| `200` | OK |
| `201` | Ressurs opprettet |
| `400` | Manglende eller ugyldig data i request |
| `404` | Aktivitet eller ressurs ikke funnet |
| `500` | Serverfeil (sjekk backend-log) |

Alle feilsvar har formen:
```json
{ "error": "Beskrivelse av feilen" }
```

**Vanlige feil:**
- `"name and username are required"` — mangler felt i POST-body
- `"No file field in request"` — form-feltet heter feil (skal være `file` / `report`)
- `"report (run-report.json) is required"` — mangler rapport-fil i upload/results
- `"Invalid JSON in report: ..."` — run-report.json er ugyldig JSON
- `"No Excel file uploaded"` — prøver å laste ned Excel før den er lastet opp
- `"AZURE_STORAGE_CONNECTION_STRING is not configured"` — Azure-miljøvariabel mangler

---

## Dataflyt — visuell oversikt

```
Grasshopper                    RamGAP Backend              Azure Blob Storage
    │                               │                              │
    │── POST /modeling/activities ──►│                              │
    │◄─ {activity_id: 13} ──────────│                              │
    │                               │                              │
    │── POST upload/excel ──────────►│── upload ────────────────────►│
    │◄─ {success: true} ────────────│   blob: projects/5/           │
    │                               │         modeling/13/excel/    │
    │  [Kjør optimering i GH]       │                              │
    │                               │                              │
    │── POST upload/results ────────►│── lagre JSON + MD i DB        │
    │   (report.json + summary.md   │                              │
    │    + ifc valgfritt) ──────────►│── upload IFC ───────────────►│
    │◄─ {success: true} ────────────│                              │
    │                               │                              │
                         RamGAP Frontend
                               │
             GET /results ──────►│── henter JSON fra DB
             GET /download/excel ►│── genererer SAS-URL (1t)
                                 │── viser grafer og nedlastingslenker
```

---

## Testscript (Python)

Et fungerende testscript som kjører hele flyten med data fra `sandbox/GH-data/`:

```
python sandbox/GH-data/test_api.py
```

Se [sandbox/GH-data/test_api.py](../sandbox/GH-data/test_api.py) for detaljer.
