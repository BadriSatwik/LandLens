# LandVerify Batch 3 — macOS

## Terminal 1 — Backend
```bash
cd ~/Downloads/LandVerify/backend
python3 -m venv venv
source venv/bin/activate
brew install tesseract
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Backend: http://127.0.0.1:8000/docs

## Terminal 2 — Frontend
```bash
cd ~/Downloads/LandVerify/frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

## Demo accounts
- Citizen: citizen@landverify.demo / citizen123
- Officer: officer@landverify.demo / officer123
- Admin: admin@landverify.demo / admin123
