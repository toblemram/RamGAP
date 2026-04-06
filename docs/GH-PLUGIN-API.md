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

---

# Tørmur (V220) — Grasshopper-arbeidsflyt

Tørmur-dimensjonering bruker V220-beregningsstandarden (Coulomb jordtrykk, Hansen bæreevne, Eurocode 7).
GH-pluginen sender **polylinje-par** (topp + bunn av mur) til backend, som henter V220-parametere fra aktiviteten, beregner seksjoner, kjører per-seksjon brute-force-optimalisering, og returnerer resultatene med detaljerte beregningsdata per seksjon.

## Tørmur-arbeidsflyt

GH-pluginen trenger bare **én forespørsel** for å kjøre en komplett tørmur-optimalisering. Prosjekt og aktivitet **må allerede eksistere** i RamGAP med V220-parametere lagret — endepunktet oppretter aldri nye prosjekter/aktiviteter. Navneoppslag er case-insensitive.

```
[GH Plugin]
    │
    ├─ 1. Send polylines +          POST /api/modeling/optimize-from-gh
    │     prosjektnavn + aktivitetsnavn
    │     (backend henter V220-parametere fra aktiviteten)
    │     (returnerer full rapport + activity_id)
    │
    ├─ 2. Last ned Excel (valgfritt) GET /api/modeling/activities/{activity_id}/export/excel
    │     (activity_id returneres i steg 1)
    │
    └─ 3. Last opp IFC (valgfritt)  POST /api/modeling/activities/{activity_id}/upload/results
          (kun ifc-felt)
```

> **Merk:** `activity_id` (int) returneres i responsen fra steg 1 og brukes kun ved filnedlasting. GH-pluginen trenger aldri å håndtere prosjekt-ID eller aktivitets-ID direkte.

---

## Tørmur-spesifikke endepunkter

### TS1. Lagre V220-parametere (RamGAP-intern)

```
POST /api/modeling/activities/{activity_id}/tormur-params
Content-Type: application/json
```

**Body — komplett V220-parametersett:**
```json
{
  "H": 3.5,
  "bt": 0.6,
  "bb": 1.5,
  "beta_deg": 0.0,
  "gamma_ite": 1.0,
  "q_k": 10.0,
  "q_last": 0.0,
  "H_last": 0.0,
  "gamma_Q": 1.3,
  "gamma_bogle": 1.15,
  "lastfaktor_gunstig": 1.0,
  "gamma_vegg": 24.0,
  "gamma_jord": 19.0,
  "gamma_fundament": 19.0,
  "phi_bak": 42.0,
  "phi_fund": 37.0,
  "delta_bak": 28.0,
  "delta_fund": 24.67,
  "adhesjon": 9.0,
  "fundamentdybde": 0.5,
  "boggilast_kN": 16.75,
  "velt_krav": 2.0,
  "gli_krav": 1.5,
  "bae_krav": 3.0,
  "friksjonsvinkel_dekke": 28.0,
  "phi_jord_dekke": 42.0,
  "gamma_jord_dekke": 19.0,
  "is_bogle": true,
  "is_H_last": false,
  "is_dekke": false
}
```

**Response `200`:**
```json
{
  "success": true,
  "activity": { ... }
}
```

---

### TS2. Hent V220-parametere (RamGAP-intern)

```
GET /api/modeling/activities/{activity_id}/tormur-params
```

**Response:**
```json
{
  "params": { ... },
  "activity": { ... }
}
```

---

### TS3. Kjør enkeltseksjon-sjekk (live preview)

```
POST /api/modeling/tormur/check
Content-Type: application/json
```

Sender V220-parametere med spesifikke `H`, `bt`, `bb`-verdier.
Returnerer detaljerte beregningsresultater for én seksjon.

**Response:**
```json
{
  "ok": true,
  "foundation_check": "OK",
  "bearing_check": "OK",
  "messages": {
    "A33": "...",
    "A34": "...",
    "D46": "...",
    "I46": "..."
  },
  "key_values": {
    "EA": 45.2,
    "T": 28.1,
    "Gvekt": 55.0,
    "RV": 110.5,
    "RH": 35.0,
    "e": 0.12,
    "qV": 88.4,
    "rb": 4.5,
    "rb_krav": 3.0,
    "b0": 1.2,
    "sigma_V": 73.7,
    "Ng": 30.0,
    "Nq": 22.0
  }
}
```

---

### T1. Kjør tørmur-optimalisering fra Grasshopper

**Dette er hovedendepunktet for GH-pluginen.** Prosjekt og aktivitet **må allerede eksistere** i RamGAP — endepunktet oppretter **ikke** nye prosjekter/aktiviteter. Oppslag er case-insensitive.

> **Forutsetning:** Opprett prosjekt og aktivitet i RamGAP, og sett V220-parametere (`Modellering → Tørmur parametere → Sett parametere`) **før** GH kjører optimaliseringen. Parameterne lastes automatisk fra aktiviteten.
>
> **Feilmeldinger:**
> - `404` — Prosjekt eller aktivitet ikke funnet (sjekk at navnene matcher RamGAP)
> - `400` — Ingen V220-parametere lagret på aktiviteten

```
POST /api/modeling/optimize-from-gh
Content-Type: application/json
```

**Body:**
```json
{
  "username":        "TBLM",
  "project_name":    "Støttemur E18",
  "activity_name":   "Kjøring 1 — april 2026",
  "top_polyline":    [[0,0,10.5], [1,0,10.3], [2,0,10.0], [3,0,9.8]],
  "bottom_polyline": [[0,0,7.0],  [1,0,6.8],  [2,0,6.5],  [3,0,6.2]],
  "interval":        1.0,
  "bt_range":        [0.4, 3.0, 0.1],
  "bb_range":        [0.4, 5.0, 0.1],
  "smooth_window":   3
}
```

| Felt | Type | Påkrevd | Beskrivelse |
|------|------|---------|-------------|
| `username` | string | **Ja** | Windows-brukernavn |
| `project_name` | string | **Ja** | Prosjektnavn — må matche navnet i RamGAP |
| `activity_name` | string | **Ja** | Aktivitetsnavn — må matche navnet i RamGAP (må ha V220-parametere lagret) |
| `top_polyline` | array | **Ja** | Topp av mur som `[[x,y,z], ...]` — minst 2 punkter |
| `bottom_polyline` | array | **Ja** | Bunn av mur som `[[x,y,z], ...]` — minst 2 punkter (brukes kun for høydeberegning) |
| `interval` | float | Nei | Avstand mellom seksjoner (m), standard `1.0` |
| `bt_range` | array | Nei | `[min, max, step]` for toppbredde-søk, standard `[0.4, 3.0, 0.1]` |
| `bb_range` | array | Nei | `[min, max, step]` for bunnbredde-søk, standard `[0.4, 5.0, 0.1]` |
| `smooth_window` | int | Nei | Glatting (sentrert glidende gjennomsnitt), standard `3` |

**Hva backend gjør:**
1. Finner prosjektet med gitt `project_name` + `username`
2. Finner aktiviteten med gitt `activity_name` under prosjektet
3. Laster V220-parametere fra aktiviteten (satt i RamGAP) — returnerer `400` hvis ingen parametere er lagret
4. Sampler `top_polyline` med gitt `interval`
4. For hvert samplingspunkt: projiserer vertikalt ned til `bottom_polyline` for å finne `height`
5. Kjører brute-force-optimalisering per seksjon (minimerer volum, `bb ≥ bt`)
6. Glatter resultater med bevegelig gjennomsnitt
7. Verifiserer at glattede verdier fortsatt passerer alle kontroller
8. Lagrer `run-report.json` og `run-summary.md` i databasen
9. Returnerer full rapport

**Response `200`:**
```json
{
  "success": true,
  "activity_id": 13,
  "report": {
    "RunId": "a1b2c3d4...",
    "CreatedUtc": "2026-03-23T08:00:00",
    "Config": { ... },
    "Sections": [
      {
        "Index": 0,
        "Station": 0.0,
        "Height": 3.5,
        "TopWidth": 0.6,
        "BottomWidth": 1.5,
        "FaceAngleDeg": 0.0,
        "VolumePerMeter": 3.675,
        "SmoothedTopWidth": 0.6,
        "SmoothedBottomWidth": 1.5,
        "SmoothedFaceAngleDeg": 0.0,
        "TopPoint": [0.0, 0.0, 10.5],
        "BottomPoint": [0.0, 0.0, 7.0],
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
        "Diagnostics": {
          "EA": 45.2,
          "T": 28.1,
          "Gvekt": 55.0,
          "RV": 110.5,
          "RH": 35.0,
          "e": 0.12,
          "qV": 88.4,
          "rb": 4.5,
          "rb_krav": 3.0,
          "b0": 1.2,
          "sigma_V": 73.7,
          "Ng": 30.0,
          "Nq": 22.0,
          "KA": 0.217,
          "KA_korr": 0.195,
          "K_delta": 0.9,
          "tan_rho_bak": 0.643,
          "tan_rho_under": 0.538,
          "foundation_check": "OK",
          "bearing_check": "OK",
          "msg_D46": "Krav til maksimal ruhet i fundamentfuge og effektiv fundamentbredde innfridd",
          "msg_I46": "Krav til maksimalt tillatt overført fundamenttrykk innfridd"
        }
      }
    ],
    "TotalLength": 3.0,
    "TotalVolume": 11.025,
    "FailedSections": 0
  },
  "summary": "## Tørmur optimeringsrapport\n...",
  "activity": { ... }
}
```

---

### T2. Last ned Excel-rapport

```
GET /api/modeling/activities/{activity_id}/export/excel
```

> `activity_id` hentes fra responsen til T1.

Returnerer en `.xlsx`-fil direkte (ikke JSON). Filen inneholder 3 ark:

| Ark | Innhold |
|-----|---------|
| Sammendrag | RunId, dato, antall seksjoner, totallengde, totalvolum, feilede seksjoner |
| Parametere | Alle V220-parametere (nøkkel/verdi) |
| Seksjoner | Stasjon, høyde, bredder, vinkel, areal, sikkerhetsfaktorer, godkjent-status |

**Response:** `200 OK` med `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

---

## Eksempel — C# med HttpClient (Tørmur)

```csharp
using System.Net.Http;
using System.Net.Http.Json;

var baseUrl  = "http://localhost:5050";
var client   = new HttpClient();
var username = Environment.UserName;

// --- Kjør tørmur-optimalisering ---
// Parametere hentes automatisk fra aktiviteten (satt i RamGAP).
// Send bare polylinjer + navn.
var tormurRequest = new
{
    username,
    project_name  = "Støttemur E18",       // ← prosjektnavn (string)
    activity_name = "Kjøring 1",            // ← aktivitetsnavn (string)
    top_polyline = new double[][]
    {
        new[] { 0.0, 0.0, 10.5 },
        new[] { 5.0, 0.0, 10.0 },
        new[] { 10.0, 0.0, 9.5 }
    },
    bottom_polyline = new double[][]
    {
        new[] { 0.0, 0.0, 7.0 },
        new[] { 5.0, 0.0, 6.5 },
        new[] { 10.0, 0.0, 6.0 }
    },
    interval = 1.0,
    bt_range = new[] { 0.4, 3.0, 0.1 },
    bb_range = new[] { 0.4, 5.0, 0.1 },
    smooth_window = 3
};

var resp = await client.PostAsJsonAsync(
    $"{baseUrl}/api/modeling/optimize-from-gh",
    tormurRequest
);
var result = await resp.Content.ReadFromJsonAsync<OptimizeResponse>()!;
int activityId = result.activity_id;   // ← lagre for nedlasting
Console.WriteLine($"Seksjoner: {result.report.Sections.Count}");

// --- Last ned Excel (bruker activity_id fra responsen) ---
var excelBytes = await client.GetByteArrayAsync(
    $"{baseUrl}/api/modeling/activities/{activityId}/export/excel"
);
File.WriteAllBytes("Tormur_rapport.xlsx", excelBytes);
```

### Hjelpeklasser for optimeringsrespons

```csharp
record OptimizeResponse(bool success, int activity_id, RunReport report, string summary);
record RunReport(
    string RunId, string CreatedUtc, Dictionary<string, object> Config,
    List<Section> Sections, double TotalLength, double TotalVolume, int FailedSections
);
record Section(
    int Index, double Station, double Height,
    double TopWidth, double BottomWidth, double FaceAngleDeg,
    double VolumePerMeter,
    double SmoothedTopWidth, double SmoothedBottomWidth, double SmoothedFaceAngleDeg,
    double[]? TopPoint, double[]? BottomPoint,
    SectionChecks Checks,
    Dictionary<string, object>? Diagnostics
);
record SectionChecks(
    double SlidingFactor, double OverturningFactor, double BearingFactor,
    bool SlidingOk, bool OverturningOk, bool BearingOk, bool AllOk,
    string GoverningCheck
);
```

---

## Geometrikonstruksjon i Grasshopper

Hvert `Section`-objekt i responsen inneholder `TopPoint` og `BottomPoint` — 3D-koordinater `[x, y, z]` for topp og bunn av muren ved den seksjonen.

### Viktig om polylinjene

- **`top_polyline`** definerer fronten av muren på toppen — dette er hjørnepunktet på topp/front av tverrsnittet.
- **`bottom_polyline`** brukes **kun** for å bestemme høyden på muren (z-differanse). Den definerer **ikke** bunnens x,y-posisjon.
- Veggen står **rett ut** (vinkelrett) fra toppolylinjen. Bredden legges langs normalvektoren.
- `TopPoint` og `BottomPoint` har **samme x, y** — kun z er forskjellig. Bunnpunktet er rett under topppunktet.

### Tverrsnitt per seksjon (symmetrisk trapesoid)

Hvert tverrsnitt er en **symmetrisk trapesoid** (4 hjørner) der **både front og bakside heller**. For å bygge tverrsnittet:

1. **Beregn murretning**: Retningsvektoren `dir` går langs murlinjen fra seksjon `i` til `i+1`.
2. **Beregn normalvektor**: `normal = CrossProduct(dir, Z-axis)`, normalisert. Denne peker vinkelrett ut fra murfronten.
3. **Beregn helningsforskjell**: `half_diff = (bb - bt) / 2`. Denne verdien forskyver bunnhjørnene slik at front- og baksiden heller likt.
4. **4 hjørnepunkter** for seksjonen:

```
TopPoint = [x, y, z_topp]    (fra responsen — murfrontens toppkant)
BottomPoint = [x, y, z_bunn]  (rett under TopPoint, kun z er annerledes)

bt = SmoothedTopWidth         (toppbredde i meter)
bb = SmoothedBottomWidth      (bunnbredde i meter)
half_diff = (bb - bt) / 2    (helningsforskjell)

Hjørne 1 (topp, front):    TopPoint
Hjørne 2 (topp, bak):      TopPoint + normal * bt
Hjørne 3 (bunn, bak):      BottomPoint + normal * (bt + bb) / 2
Hjørne 4 (bunn, front):    BottomPoint - normal * half_diff
```

> Tverrsnittet er en symmetrisk trapesoid: frontsiden og baksiden heller **likt** utover.
> Når `bt == bb` (lik bredde topp og bunn) blir formen et parallellogram.
> Bredden ved toppen er `bt`, bredden ved bunnen er `bb`.

### Lofting mellom seksjoner

For å bygge 3D-volumet av muren:

1. Bygg trapesoid-profiler for hver seksjon (som beskrevet over)
2. Bruk **Loft** mellom naboprofiler (seksjon 0→1, 1→2, 2→3, osv.)
3. Eventuelt **Cap** endene for et lukket volum

### Pseudokode (C#/GH)

```csharp
var sections = report.Sections;

for (int i = 0; i < sections.Count; i++)
{
    var sec = sections[i];
    var top = new Point3d(sec.TopPoint[0], sec.TopPoint[1], sec.TopPoint[2]);
    var bot = new Point3d(sec.BottomPoint[0], sec.BottomPoint[1], sec.BottomPoint[2]);

    // Retning langs mur (bruk neste seksjon, eller forrige for siste)
    Vector3d dir;
    if (i < sections.Count - 1)
    {
        var nextTop = new Point3d(sections[i + 1].TopPoint[0],
                                   sections[i + 1].TopPoint[1],
                                   sections[i + 1].TopPoint[2]);
        dir = nextTop - top;
    }
    else
    {
        var prevTop = new Point3d(sections[i - 1].TopPoint[0],
                                   sections[i - 1].TopPoint[1],
                                   sections[i - 1].TopPoint[2]);
        dir = top - prevTop;
    }
    dir.Unitize();

    // Normal vinkelrett på murlinjen (horisontal)
    var normal = Vector3d.CrossProduct(dir, Vector3d.ZAxis);
    normal.Unitize();

    double bt = sec.SmoothedTopWidth;
    double bb = sec.SmoothedBottomWidth;
    double halfDiff = (bb - bt) / 2.0;

    // 4 hjørner (symmetrisk trapesoid — front og bakside heller likt)
    var p1 = top;                                      // topp, front
    var p2 = top + normal * bt;                        // topp, bak
    var p3 = bot + normal * (bt + bb) / 2.0;           // bunn, bak
    var p4 = bot - normal * halfDiff;                  // bunn, front

    var profile = new Polyline(new[] { p1, p2, p3, p4, p1 });
    profiles.Add(profile.ToNurbsCurve());
}

// Loft alle profiler til en Brep
var loft = Brep.CreateFromLoft(profiles, Point3d.Unset, Point3d.Unset,
                                LoftType.Straight, false);
```

### Viktig

- `TopPoint` og `BottomPoint` er alltid `[x, y, z]` i prosjektets koordinatsystem (samme som input-polylinjene).
- For seksjoner med `Height == 0` vil `TopPoint[2] == BottomPoint[2]` — disse kan hoppes over i geometrien.
- `TopPoint` / `BottomPoint` kan være `null` for seksjoner som ikke ble samplet fra polylinjer (f.eks. manuelt opprettet). Sjekk for `null` før bruk.
