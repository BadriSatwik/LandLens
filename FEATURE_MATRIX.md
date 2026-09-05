# LandVerify — SIH26018 Feature Matrix

| Requirement | Implementation | Boundary |
|---|---|---|
| RBAC | Citizen/Officer/Admin dashboards and API authorization | Demo identities unless connected to a real IdP |
| Document repository | Persistent local storage + metadata + authenticated download | Replace local storage with S3/object storage in production |
| PDF/image OCR | PyMuPDF + Tesseract + image preprocessing | OCR quality depends on local language packs |
| Multilingual OCR | English/Telugu/Hindi/Kannada/Tamil/Bengali/Marathi/Gujarati options | Requested pack must be installed |
| Handwriting | Dedicated preprocessing mode + confidence routing | Not a dedicated handwriting foundation model |
| Field classification | Extended land-domain field extractor and multilingual labels | Rule-based classifier in the prototype |
| Confidence | Word-level Tesseract confidence aggregated to fields | Statistical OCR confidence, not legal certainty |
| Validation | Normalization, exact match, fuzzy review, business/reference checks | Demo reference DB unless external connector configured |
| Duplicate detection | Weighted similarity screening | Production should add domain-specific duplicate rules |
| Human verification | Officer queue, corrections, approve/reject/request correction | Workflow is local prototype |
| Learning | Corrections stored and reused as feedback-derived mappings | No autonomous model retraining |
| Audit | Append-only audit event table | Add tamper-evident external logging in production |
| Analytics | Processing, verification, validation, confidence, errors, state/district progress | Metrics are based on prototype data |
| GIS | GeoJSON parcel viewer + Admin import | Built-in parcels are demo geometry |
| LRMS/DILRMP | Configurable adapter layer with mock/local mode and optional HTTP delivery | Live government connectivity requires approved endpoints/credentials |
| Government APIs | Adapter boundary + environment configuration | No live government system is embedded |
