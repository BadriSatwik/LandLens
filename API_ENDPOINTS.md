# LandVerify API endpoints

FastAPI Swagger: `/docs`
OpenAPI schema: `/openapi.json`

## Public
- `GET /` — service info
- `GET /health` — health check
- `POST /login` — bearer-token login

## Authenticated
- `GET /me`
- `GET /api/endpoints`
- `GET /ocr/languages`
- `POST /extract`
- `GET /documents`
- `GET /documents/{document_id}`
- `GET /documents/{document_id}/download`
- `POST /validate`
- `GET /audit`
- `GET /dashboard/stats`
- `GET /gis/parcels`
- `GET /gis/parcels/{survey_number}`
- `GET /gis/compare/{document_id}`

## Officer/Admin
- `GET /records`
- `GET /records/{survey_number}`
- `GET /verification/queue`
- `POST /verification/{document_id}`
- `GET /duplicates`
- `GET /duplicates/{document_id}`
- `POST /learning/feedback`
- `GET /learning/feedback`
- `GET /learning/suggestions`
- `GET /integrations/status`
- `GET /integrations/logs`
- `POST /integrations/lrms/sync/{document_id}`
- `POST /integrations/dilrmp/export/{document_id}`

## Admin
- `GET /dashboard/analytics`
- `POST /gis/import`
- `GET /admin/users`
- `POST /admin/users`
- `GET /admin/system-export`

All protected endpoints require `Authorization: Bearer <token>`.
