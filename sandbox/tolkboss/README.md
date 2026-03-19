# tolkboss

Standalone desktop tool for downloading SND files from Fieldmanager and
visualising depth profiles.

## Status

Prototype — the SND parser is being migrated into
`backend/activities/geotolk/parsing/snd_parser.py`.

## Usage

```bash
pip install -r requirements.txt   # customtkinter, requests, matplotlib
python main.py
```

## Files

| File              | Description                                |
|-------------------|--------------------------------------------|
| `main.py`         | App entry point                            |
| `gui_download.py` | Download tab (Fieldmanager API)            |
| `gui_plot.py`     | Plot tab (depth-profile chart)             |
| `snd_parser.py`   | SND file parser (source for migration)     |
| `api_client.py`   | Fieldmanager API client                    |
