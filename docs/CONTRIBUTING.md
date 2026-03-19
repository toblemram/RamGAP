# Contributing

## Code Style

- **Language**: All code, comments, and docstrings must be written in English.
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes,
  `UPPER_SNAKE_CASE` for constants.
- **File header**: Every Python file must start with a module-level docstring
  describing its purpose (see template below).

## File Header Template

```python
# -*- coding: utf-8 -*-
"""
<Module name>
=============
<One-sentence description of what this file contains.>

Longer description, responsibilities, and any important notes.
"""
```

## Adding a New Activity

1. Create a folder under `backend/activities/<activity_name>/`.
2. Add `__init__.py`, `routes.py`, `service.py`, and any sub-folders needed.
3. Register the blueprint in `backend/app.py`.
4. Add a matching page under `frontend/pages/<activity_name>.py`.
5. Add HTTP methods for the new endpoints in `frontend/components/api_client.py`.
6. Add unit tests under `tests/unit/`.

## Parking Work in Progress

Code that is not ready for the main application goes in `sandbox/`. Create a
new sub-folder with a descriptive name (e.g. `sandbox/my_feature/`). This keeps
`backend/` and `frontend/` clean and avoids dead imports.

## Branch Strategy

- `main` — stable, tested code only
- `dev` — integration branch
- `feature/<name>` — individual features
