# LandVerify — SIH26018 Hackathon Final (v6.0.0)

LandVerify is an AI-assisted prototype for intelligent land-record digitization, validation and human verification.

## Core demo flow

`Login → Role workspace → Upload → Field-aware OCR → Confidence → Human review → Official-record validation → Duplicate screening → Decision → Audit`

## Included features

- JWT-style bearer authentication with PBKDF2 password hashing.
- Citizen, Officer and Admin workspaces with role-based backend permissions.
- Persistent document repository with metadata and authenticated download.
- PDF/JPG/JPEG/PNG ingestion.
- Field-aware multi-pass OCR designed for labelled land-register documents.
- Blue/purple stamp suppression to reduce OCR interference from seals/stamps.
- Land-record template OCR mode plus general printed and handwriting-oriented modes.
- English, Telugu, Hindi, Kannada, Tamil, Bengali, Marathi and Gujarati OCR options when Tesseract packs are installed.
- Extended land-record schema: owner, survey, khasra, khata, plot, village, tehsil, district, area, classification, ownership, mutation, document and registration data.
- Field-level OCR confidence and low-confidence highlighting.
- Normalized validation, cross-database verification and fuzzy review states.
- Similarity-based duplicate and near-duplicate screening.
- Officer verification queue with correction, approval, rejection and request-correction actions.
- Human corrections persisted as learning feedback.
- Audit trail.
- Admin analytics with processing volume, validation outcomes, confidence, errors and geographic progress.
- GIS / GeoJSON parcel viewer and Admin import endpoint.
- LRMS / DILRMP / government integration adapters with explicit mock/live status.
- Live API endpoint catalog in the UI plus FastAPI Swagger at `/docs`.
- Demo seed records so dashboards are not empty on a fresh deployment.

## Demo accounts

- Citizen: `citizen@landverify.demo` / `citizen123`
- Officer: `officer@landverify.demo` / `officer123`
- Admin: `admin@landverify.demo` / `admin123`

## Local macOS run

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
brew install tesseract
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Backend: `http://127.0.0.1:8000`
Swagger: `http://127.0.0.1:8000/docs`

### Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

## Recommended demo document

Use `sample_data/demo_land_record.png` and select:

- OCR language: `English`
- Recognition mode: `Land-record template`

Expected key extraction:

```text
Owner Name      Ravi Kumar
Survey Number   145/2
Village         Kamareddy
Area            2.5 acres
Document Number DOC-2026-1452
```

The prototype intentionally does not claim 100% arbitrary-document OCR. It uses a field-aware, multi-pass strategy for supported layouts and routes uncertain fields to human verification.

## Deployment on Render

`render.yaml` contains both services:

- `landverify-api` — Docker web service from `backend/`
- `landverify` — React/Vite static site from `frontend/`

After deploying the API, copy its URL into the frontend `VITE_API_URL`. Then set the backend `FRONTEND_URL` to the public frontend URL and redeploy the API.

## API

See `API_ENDPOINTS.md` for the endpoint inventory. The live interactive specification is available at `/docs` on the backend.

## Testing

`backend/test_batch4.py` is the regression suite. It covers authentication, RBAC, real sample OCR, image/PDF extraction, validation, repository, human verification, feedback, audit, analytics, duplicates, GIS and integrations.

## Prototype limitations

Official LRMS/DILRMP credentials, approved government endpoints, official cadastral datasets and dedicated production handwriting foundation models are external dependencies. The prototype provides integration boundaries and demo adapters rather than pretending those external systems are connected.
