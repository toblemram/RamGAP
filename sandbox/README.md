# Sandbox

Prototype scripts, standalone tools, and experimental code that is not yet
part of the main platform.

Everything here is for **exploration and reference only**. When a prototype
is ready to be integrated into the platform, move the relevant logic into
`backend/activities/<name>/` and add proper tests.

## Contents

| Folder            | Description                                              |
|-------------------|----------------------------------------------------------|
| `plaxis_scripts/` | Standalone Plaxis extraction scripts                     |
| `chatplax/`       | Tkinter-based Plaxis chat prototype (OpenAI)             |
| `plaxchat2/`      | Advanced chat prototype with RAG (FAISS knowledge base)  |
| `tolkboss/`       | Standalone SND download and plot tool (CustomTkinter)    |
| `pyqt_prototype/` | Early PyQt5 desktop app prototype                        |
| `experiments/`    | One-off test scripts and snippets                        |

## Rules

- Do **not** import from `sandbox/` in the main `backend/` or `frontend/`.
- Each sub-folder should have its own `README.md` and, if needed,
  a separate `requirements.txt`.
