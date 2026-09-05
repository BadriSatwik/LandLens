# Render deployment

## Backend — Web Service
Repository: `BadriSatwik/LandLens`
Branch: `main`
Runtime: `Docker`
Root Directory: `backend`
Dockerfile Path: `Dockerfile`
Health Check Path: `/health`

Environment variables:
- `LANDVERIFY_SECRET` — generate a strong random value.
- `FRONTEND_URL` — exact public URL of the Render frontend static site.
- Optional `LANDVERIFY_LRMS_URL`, `LANDVERIFY_DILRMP_URL`, `LANDVERIFY_GOV_API_URL` for approved external connectors.

## Frontend — Static Site
Repository: `BadriSatwik/LandLens`
Branch: `main`
Root Directory: `frontend`
Build Command: `npm install && npm run build`
Publish Directory: `dist`

Environment variable:
- `VITE_API_URL=https://YOUR-BACKEND.onrender.com`

After the frontend is deployed, update the backend `FRONTEND_URL` to the actual frontend URL and redeploy the backend.

## Verification
1. Open backend `/health`.
2. Open backend `/docs`.
3. Open the frontend URL.
4. Test Citizen, Officer and Admin logins.
5. Upload `sample_data/demo_land_record.png` and confirm `Ravi Kumar`, `145/2`, `Kamareddy`, `2.5 acres`, and `DOC-2026-1452` are extracted in Land-record template mode.
