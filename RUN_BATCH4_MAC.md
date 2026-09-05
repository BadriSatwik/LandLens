# Run LandVerify Batch 4 on macOS

## Terminal 1 — backend

```bash
cd ~/Downloads/LandVerify_BATCH4_FINAL/backend
python3 -m venv venv
source venv/bin/activate
brew install tesseract
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Backend: http://127.0.0.1:8000
Swagger: http://127.0.0.1:8000/docs

## Terminal 2 — frontend

```bash
cd ~/Downloads/LandVerify_BATCH4_FINAL/frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

## Demo users

Citizen: citizen@landverify.demo / citizen123
Officer: officer@landverify.demo / officer123
Admin: admin@landverify.demo / admin123
