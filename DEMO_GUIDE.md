# LandVerify — 5 Minute SIH Demo Script

## 1. Login as Officer

Use:

`officer@landverify.demo` / `officer123`

Show the role-specific Officer workspace and the verification queue.

## 2. Upload a land record

Open `Validator` and upload the sample land document.

Recommended scenario:

- Owner: Ravi Kumar
- Survey number: 145/2
- Village: Kamareddy
- Area: 2.5 acres
- Official owner in the reference record: Ramesh Kumar

## 3. Show OCR confidence

Highlight the field-level confidence values and explain that uncertain fields can be reviewed instead of being blindly trusted.

## 4. Human verification

Correct or confirm an extracted field, save the correction, and explain that the correction is recorded as feedback.

## 5. Validate

Show the field-by-field comparison:

- Survey number — match
- Owner name — discrepancy
- Village — match
- Area — match
- Missing/uncertain fields — review/not detected

Explain that the consistency score is a comparison metric, not a statement of legal ownership.

## 6. Officer decision

Open `Verification Queue` and demonstrate:

- Save correction
- Duplicate scan
- Request correction
- Reject
- Approve

## 7. Audit trail

Open `Audit` and show the chain of actions and timestamps.

## 8. Admin

Logout and sign in as:

`admin@landverify.demo` / `admin123`

Show:

- Analytics
- Records
- Users
- Audit
- GIS
- Integrations
- Learning feedback

## 9. Key message

LandVerify is an AI-assisted workflow, not just OCR: it digitizes records, estimates extraction confidence, routes uncertainty to human verification, cross-checks against reference records, detects discrepancies/duplicates, records decisions, and exposes integration/API boundaries.

## Technical honesty

The project uses demo/local reference data. LRMS/DILRMP and government integrations are adapter-ready but are not presented as live government connections. GIS uses demo GeoJSON unless an approved dataset is imported. Handwriting uses handwriting-oriented preprocessing; production-grade handwriting models and autonomous model retraining require appropriate models/data.
