# chatplax

Tkinter-based chat prototype that uses OpenAI to generate Plaxis Python code
from plain-language instructions and executes it against a live Plaxis session.

## Status

Prototype — being superseded by the AI Assistant activity in the main platform.

## Usage

```bash
pip install -r requirements.txt
python app.py
```

Requires:
- A running Plaxis Input session
- `OPENAI_API_KEY` set in `.env`
