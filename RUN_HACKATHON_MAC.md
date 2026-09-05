# LandVerify — Hackathon Final (macOS)

## Prerequisites

- Python 3.11+ recommended (the project also works with the tested Python 3.14 environment used during development).
- Node.js 20+ recommended.
- Homebrew.
- Tesseract for OCR.

Install the OCR engine once:

```bash
brew install tesseract
```

Optional language packs can be installed separately. English is enough for the included demo dataset.

## Terminal 1 — Backend

```bash
cd ~/Downloads/LandVerify/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Backend: http://127.0.0.1:8000
Swagger: http://127.0.0.1:8000/docs

## Terminal 2 — Frontend

```bash
cd ~/Downloads/LandVerify/frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

## Demo accounts

```text
Citizen
citizen@landverify.demo
citizen123

Officer
officer@landverify.demo
officer123

Admin
admin@landverify.demo
admin123
```

## Reset the local demo database

From `backend/`:

```bash
python reset_demo.py
```

This removes local demo runtime data and reseeds the official reference records and demo users.
