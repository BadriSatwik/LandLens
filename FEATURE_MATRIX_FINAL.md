# LandVerify — SIH26018 Final Feature Matrix

| Capability | Prototype status | Notes |
|---|---|---|
| Login | Implemented | JWT-style bearer tokens with role claims |
| RBAC | Implemented | Citizen / Officer / Admin |
| Document upload | Implemented | PDF/JPG/JPEG/PNG |
| Document repository | Implemented | Persistent local storage + metadata |
| OCR | Implemented | Tesseract |
| PDF OCR | Implemented | PDF pages rendered and OCRed |
| Structured extraction | Implemented | Domain-field extraction |
| Land-domain fields | Implemented | Owner, survey, khasra, khata, plot, village, tehsil, district, state, area, classification, ownership, mutation, document and registration |
| Confidence scoring | Implemented | Field-level estimated OCR confidence |
| Human verification | Implemented | Officer review/edit/decision workflow |
| Validation | Implemented | Normalized comparison + review states |
| Duplicate detection | Implemented | Weighted similarity screening |
| Audit trail | Implemented | Persistent actor/action/time records |
| Learning feedback | Implemented | Correction dataset + deterministic suggestion view |
| Analytics | Implemented | Volume, outcomes, confidence, errors, geography |
| Multilingual OCR | Prototype | Language selection/fallback depends on installed Tesseract packs |
| Handwriting | Prototype | Handwriting-oriented preprocessing, not a dedicated production handwriting model |
| GIS / cadastral | Prototype | GeoJSON parcel layer, demo geometry, import endpoint |
| LRMS | Adapter/demo | Mock mode until an approved endpoint is configured |
| DILRMP | Adapter/demo | Mock export until an approved endpoint is configured |
| Government APIs | Adapter boundary | Configurable external REST boundary |
| Official government datasets | Not bundled | Requires approved access/data |
| Autonomous model retraining | Not bundled | Feedback is captured for future training/evaluation |
