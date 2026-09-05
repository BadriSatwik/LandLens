# LandVerify Batch 4 Test Report

Date: 2026-09-04

## Passed tests
- Python bytecode compilation for all backend modules.
- FastAPI health endpoint under a real Uvicorn process.
- Fresh SQLite initialization and seeded official records.
- PBKDF2-hashed demo authentication for Citizen, Officer and Admin.
- RBAC: citizen blocked from officer/admin routes; officer/admin access verified.
- Image OCR and structured extraction on a land-record PNG.
- PDF OCR and structured extraction.
- Handwriting-oriented OCR preprocessing path.
- Multilingual OCR language selection/fallback path.
- Extended land fields including survey, khasra, khata, plot, tehsil, classification, ownership and mutation fields.
- Field-level OCR confidence generation.
- Validation against reference records, including discrepancy detection and normalization.
- Persistent document repository and authenticated document download.
- Verification queue and officer approval workflow.
- Human correction feedback capture.
- Duplicate screening.
- Audit logging.
- Admin analytics including state and district progress.
- GIS parcel lookup.
- Admin GeoJSON import.
- LRMS and DILRMP adapter calls in local/mock mode.
- Admin user creation with persistent hashed credentials.

## Browser build note
A full `npm install` / Vite browser build could not be executed in this build environment because external npm registry access was unavailable. The frontend source and package manifest are included for local installation on the user's Mac.
