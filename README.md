# PersonalBrain — Web UI

This adds a tiny Flask-based web UI to run your local assistant. It uses your existing `brain.py` logic and vector search.

Files added:
- `app.py` — Flask server with `/` UI and `/api/chat` endpoint
- `templates/index.html` — simple chat UI
- `static/chat.js` — frontend JS to call the API
- `static/style.css` — UI styles
- `requirements.txt` — Flask dependency

How to run (Windows PowerShell):

1. Activate your virtual environment (from the project root):

```powershell
.\venv\Scripts\Activate.ps1
```

2. Install requirements (only needed once):

```powershell
pip install -r requirements.txt
```

3. Start the server:

```powershell
python app.py
```

4. Open http://127.0.0.1:5000 in your browser and ask questions.

Notes:
- The server imports `brain.py` to reuse its `search`, `format_context`, `prompt`, and `model` objects. Ensure `brain.py` works standalone.
- If you run into import errors, confirm your venv is activated and required packages are installed there.
