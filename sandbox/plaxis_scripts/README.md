# plaxis_scripts

Standalone Plaxis extraction scripts — the original working scripts
that were developed before the platform was built.

These are the source of truth for the extraction logic that is being
migrated into `backend/activities/plaxis/extraction/`.

## Files

| File                          | Description                                      |
|-------------------------------|--------------------------------------------------|
| `main.py`                     | Entry point — runs a full extraction job         |
| `level1_extractInfo.py`       | Fetch phases and structure names (Level 1)        |
| `level5_getData.py`           | Trigger and read Plaxis Output results (Level 5)  |
| `level5_extractPlaxisResults.py` | Parse raw result data into structured dicts   |
| `level5_printResults.py`      | Write results to Excel                           |

## Usage

Run directly from a Plaxis Python environment:

```bash
python main.py
```

Make sure `plxscripting` is available before running.
