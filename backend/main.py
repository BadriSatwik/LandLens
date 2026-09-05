from __future__ import annotations
from difflib import SequenceMatcher
from pathlib import Path
import json, os, re, uuid

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from auth import authenticate_user, create_access_token, get_current_user, require_roles, seed_demo_users, hash_password
from database import *
from integrations import dilrmp_export, integration_status, lrms_sync
from ocr import SUPPORTED_LANGUAGES, available_tesseract_languages, extract_land_record
from learning import learned_corrections

APP_VERSION = "6.0.0"
app = FastAPI(
    title="LandVerify API",
    description="AI-assisted Intelligent Land Record Digitization and Validation System",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

_frontends = ["http://localhost:5173", "http://127.0.0.1:5173"]
for raw in [os.getenv("FRONTEND_URL", ""), os.getenv("FRONTEND_URLS", "")]:
    _frontends.extend([x.strip().rstrip("/") for x in raw.split(",") if x.strip()])
app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(set(_frontends)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LandRecord(BaseModel):
    owner_name: str | None = None
    survey_number: str
    village: str | None = None
    district: str | None = None
    tehsil: str | None = None
    khasra_number: str | None = None
    khata_number: str | None = None
    plot_number: str | None = None
    area: str | None = None
    land_classification: str | None = None
    ownership_type: str | None = None
    mutation_status: str | None = None
    document_number: str | None = None
    registration_date: str | None = None

class VerificationAction(BaseModel):
    status: str
    remarks: str = Field(default="", max_length=2000)

class FeedbackRequest(BaseModel):
    document_id: str
    field_name: str
    corrected_value: str = Field(min_length=1, max_length=500)
    notes: str = Field(default="", max_length=2000)

class UserCreate(BaseModel):
    email: str
    name: str
    role: str
    password: str = Field(min_length=8, max_length=128)

FIELD_NAMES = list(LandRecord.model_fields.keys())


def norm(v):
    if v is None:
        return ""
    s = str(v).strip().lower()
    s = re.sub(r"\bacres?\b", "acres", s)
    return re.sub(r"[^\w/.-]", "", s)


def sim(a, b):
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def compare(name, uploaded, existing):
    if uploaded is None or str(uploaded).strip() == "":
        return {"status": "not_detected", "message": f"{name} was not detected from the document"}
    if existing is None:
        return {"status": "reference_unavailable", "message": f"No reference value exists for {name.lower()}"}
    if norm(uploaded) == norm(existing):
        return {"status": "pass", "message": f"{name} matches the existing record"}
    score = sim(uploaded, existing)
    if score >= 0.90:
        return {"status": "review", "message": f"{name} is very similar ({score:.0%} similarity); review for OCR noise"}
    return {"status": "fail", "message": f"Uploaded record says {uploaded}, existing record says {existing}"}


def role_check_doc(doc, user):
    if not doc:
        raise HTTPException(404, "Document not found")
    if user["role"] == "citizen" and doc["uploaded_by"] != user["email"]:
        raise HTTPException(403, "You cannot access this document")


@app.on_event("startup")
def startup():
    initialize_database()
    seed_demo_users()
    seed_demo_documents()

@app.get("/")
def root():
    return {"message": "LandVerify API is running", "status": "ok", "version": APP_VERSION, "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "healthy", "version": APP_VERSION}

@app.get("/api/endpoints")
def endpoint_catalog(user=Depends(get_current_user)):
    return {
        "version": APP_VERSION,
        "docs": "/docs",
        "endpoints": [
            {"method":"POST","path":"/login","roles":["public"],"description":"Authenticate and issue a bearer token"},
            {"method":"GET","path":"/me","roles":["citizen","officer","admin"],"description":"Return current user"},
            {"method":"GET","path":"/ocr/languages","roles":["citizen","officer","admin"],"description":"Show supported/installed OCR language packs"},
            {"method":"POST","path":"/extract","roles":["citizen","officer","admin"],"description":"Upload a document and extract structured fields"},
            {"method":"GET","path":"/documents","roles":["citizen","officer","admin"],"description":"List accessible documents"},
            {"method":"GET","path":"/documents/{document_id}","roles":["citizen","officer","admin"],"description":"Get document metadata and extracted fields"},
            {"method":"GET","path":"/documents/{document_id}/download","roles":["citizen","officer","admin"],"description":"Download original document"},
            {"method":"GET","path":"/records","roles":["officer","admin"],"description":"List official reference records"},
            {"method":"GET","path":"/records/{survey_number}","roles":["officer","admin"],"description":"Lookup official record"},
            {"method":"POST","path":"/validate","roles":["citizen","officer","admin"],"description":"Validate extracted fields against official records"},
            {"method":"GET","path":"/verification/queue","roles":["officer","admin"],"description":"List records awaiting human verification"},
            {"method":"POST","path":"/verification/{document_id}","roles":["officer","admin"],"description":"Approve, reject, or request correction"},
            {"method":"GET","path":"/duplicates","roles":["officer","admin"],"description":"Scan official records for duplicates"},
            {"method":"GET","path":"/duplicates/{document_id}","roles":["officer","admin"],"description":"Scan one document for duplicate candidates"},
            {"method":"POST","path":"/learning/feedback","roles":["officer","admin"],"description":"Persist a human correction for future learning"},
            {"method":"GET","path":"/learning/feedback","roles":["officer","admin"],"description":"List human corrections"},
            {"method":"GET","path":"/learning/suggestions","roles":["officer","admin"],"description":"Show learned correction categories"},
            {"method":"GET","path":"/audit","roles":["citizen","officer","admin"],"description":"Read audit history"},
            {"method":"GET","path":"/dashboard/stats","roles":["citizen","officer","admin"],"description":"Role-scoped dashboard statistics"},
            {"method":"GET","path":"/dashboard/analytics","roles":["admin"],"description":"System analytics and geographic progress"},
            {"method":"GET","path":"/gis/parcels","roles":["citizen","officer","admin"],"description":"List cadastral parcels"},
            {"method":"GET","path":"/gis/parcels/{survey_number}","roles":["citizen","officer","admin"],"description":"Lookup a parcel"},
            {"method":"GET","path":"/gis/compare/{document_id}","roles":["citizen","officer","admin"],"description":"Compare document land area with parcel"},
            {"method":"POST","path":"/gis/import","roles":["admin"],"description":"Import approved GeoJSON parcel data"},
            {"method":"GET","path":"/integrations/status","roles":["officer","admin"],"description":"Show LRMS/DILRMP/GIS adapter state"},
            {"method":"GET","path":"/integrations/logs","roles":["officer","admin"],"description":"Read integration activity"},
            {"method":"POST","path":"/integrations/lrms/sync/{document_id}","roles":["officer","admin"],"description":"Sync a document to LRMS adapter"},
            {"method":"POST","path":"/integrations/dilrmp/export/{document_id}","roles":["officer","admin"],"description":"Export a document to DILRMP adapter"},
            {"method":"GET","path":"/admin/users","roles":["admin"],"description":"List users"},
            {"method":"POST","path":"/admin/users","roles":["admin"],"description":"Create a user"},
            {"method":"GET","path":"/admin/system-export","roles":["admin"],"description":"Export system snapshot"},
        ],
    }

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(401, "Incorrect email or password")
    token = create_access_token(user)
    add_audit(user["email"], user["role"], "LOGIN", "", "Successful login")
    return {"success": True, "access_token": token, "token_type": "bearer", "user": user}

@app.get("/me")
def me(user=Depends(get_current_user)):
    return user

@app.get("/ocr/languages")
def ocr_languages(user=Depends(get_current_user)):
    installed = available_tesseract_languages()
    return {"supported":[{"code":c,"label":m["label"],"installed":c in installed} for c,m in SUPPORTED_LANGUAGES.items()],"installed":installed}

@app.post("/extract")
async def extract(file: UploadFile = File(...), language: str = Form("auto"), mode: str = Form("land_record"), user=Depends(get_current_user)):
    ext = Path(file.filename or "").suffix.lower()
    allowed = {".jpg", ".jpeg", ".png", ".pdf"}
    if ext not in allowed:
        raise HTTPException(400, "Only PDF, JPG, JPEG and PNG are supported")
    data = await file.read()
    if not data:
        raise HTTPException(400, "The uploaded document is empty")
    if len(data) > 15 * 1024 * 1024:
        raise HTTPException(413, "Document is larger than the 15 MB demo limit")
    doc_id = f"LV-{uuid.uuid4().hex[:12].upper()}"
    folder = STORAGE_DIR / doc_id
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"original{ext}"
    path.write_bytes(data)
    try:
        result = extract_land_record(str(path), language, mode)
        result["learning_adjustments"] = {}
        insert_document(
            doc_id,
            original_filename=file.filename or "document",
            stored_path=str(path),
            mime_type=file.content_type or "application/octet-stream",
            file_size=len(data),
            uploaded_by=user["email"],
            uploaded_role=user["role"],
            language_code=result["language_used"],
            language_status=result["language_status"],
            ocr_mode=result["ocr_mode"],
            recognition_note=result["recognition_note"],
            extracted_fields=result["fields"],
            confidence=result["confidence"],
            raw_text=result["raw_text"],
            survey_number=result["fields"].get("survey_number"),
        )
        add_audit(user["email"], user["role"], "DOCUMENT_EXTRACTED", doc_id, json.dumps({"filename":file.filename,"overall_confidence":result["overall_confidence"],"language":result["language_used"],"mode":mode}))
        return {"success": True, "document_id": doc_id, "filename": file.filename, **result}
    except Exception as exc:
        path.unlink(missing_ok=True)
        raise HTTPException(500, f"Document processing failed: {exc}")

@app.get("/documents")
def documents(user=Depends(get_current_user)):
    return {"documents": list_documents_for_user(user["email"]) if user["role"] == "citizen" else list_documents_all()}

@app.get("/documents/{document_id}")
def document_detail(document_id, user=Depends(get_current_user)):
    doc = get_document(document_id)
    role_check_doc(doc, user)
    return doc

@app.get("/documents/{document_id}/download")
def document_download(document_id, user=Depends(get_current_user)):
    from fastapi.responses import FileResponse
    doc = get_document(document_id)
    role_check_doc(doc, user)
    path = Path(doc["stored_path"])
    if not path.exists():
        raise HTTPException(404, "Stored document file is missing")
    add_audit(user["email"], user["role"], "DOCUMENT_DOWNLOADED", document_id, "Original document downloaded")
    return FileResponse(path, media_type=doc["mime_type"], filename=doc["original_filename"])

@app.get("/records")
def records(user=Depends(require_roles("officer", "admin"))):
    return {"records": list_records()}

@app.get("/records/{survey_number:path}")
def record(survey_number, user=Depends(require_roles("officer", "admin"))):
    r = find_record_by_survey_number(survey_number)
    return {"found": bool(r), "record": r} if r else {"found": False, "message": "No land record found"}

@app.post("/validate")
def validate(record: LandRecord, document_id: str | None = None, user=Depends(get_current_user)):
    if document_id:
        role_check_doc(get_document(document_id), user)
    existing = find_record_by_survey_number(record.survey_number)
    if not existing:
        resp = {"score":0,"status":"not_found","checks":{"survey_number":{"status":"fail","message":f"Survey number {record.survey_number} was not found in the records"}},"existing_record":None}
    else:
        payload = record.model_dump()
        checks = {"survey_number": compare("Survey number", payload.get("survey_number"), existing.get("survey_number"))}
        for key in FIELD_NAMES:
            if key == "survey_number":
                continue
            checks[key] = compare(key.replace("_", " ").title(), payload.get(key), existing.get(key))
        comparable = [c for c in checks.values() if c["status"] not in {"not_detected","reference_unavailable"}]
        passed = sum(c["status"] == "pass" for c in comparable)
        review = sum(c["status"] == "review" for c in comparable)
        fails = sum(c["status"] == "fail" for c in comparable)
        score = round(passed / len(comparable) * 100) if comparable else 0
        status = "discrepancy" if fails else ("warning" if review else ("insufficient_data" if not comparable else "valid"))
        resp = {"score":score,"status":status,"checks":checks,"existing_record":existing}
    if document_id:
        update_validation(document_id, resp["score"], resp["status"], resp["checks"])
        add_audit(user["email"], user["role"], "VALIDATED", document_id, json.dumps({"score":resp["score"],"status":resp["status"]}))
    return resp

@app.get("/verification/queue")
def queue(user=Depends(require_roles("officer", "admin"))):
    return {"documents": list_verification_queue()}

@app.post("/verification/{document_id}")
def verify(document_id, action: VerificationAction, user=Depends(require_roles("officer", "admin"))):
    if action.status not in {"approved", "rejected", "request_correction"}:
        raise HTTPException(400, "Invalid verification status")
    doc = get_document(document_id)
    role_check_doc(doc, user)
    update_verification(document_id, action.status, action.remarks, user["email"])
    add_audit(user["email"], user["role"], f"VERIFICATION_{action.status.upper()}", document_id, action.remarks)
    return {"success": True, "status": action.status}

@app.post("/learning/feedback")
def feedback(req: FeedbackRequest, user=Depends(require_roles("officer", "admin"))):
    doc = get_document(req.document_id)
    role_check_doc(doc, user)
    if req.field_name not in FIELD_NAMES:
        raise HTTPException(400, "Unsupported land-record field")
    original = doc["extracted_fields"].get(req.field_name)
    conf = doc["confidence"].get(req.field_name)
    fields = dict(doc["extracted_fields"])
    fields[req.field_name] = req.corrected_value
    update_extracted_fields(req.document_id, fields)
    add_feedback(req.document_id, user["email"], user["role"], req.field_name, original, req.corrected_value, conf, req.notes)
    add_audit(user["email"], user["role"], "FIELD_CORRECTED", req.document_id, json.dumps({"field":req.field_name,"from":original,"to":req.corrected_value}))
    return {"success":True,"field_name":req.field_name,"original_value":original,"corrected_value":req.corrected_value}

@app.get("/learning/feedback")
def feedback_list(document_id: str | None = None, user=Depends(require_roles("officer", "admin"))):
    return {"feedback": list_feedback(document_id)}

@app.get("/learning/suggestions")
def feedback_suggestions(user=Depends(require_roles("officer", "admin"))):
    return {"learned_corrections": learned_corrections()}

@app.get("/audit")
def audit(document_id: str | None = None, user=Depends(get_current_user)):
    if user["role"] == "admin":
        return {"logs": list_audit_logs(record_id=document_id)}
    if document_id:
        role_check_doc(get_document(document_id), user)
        return {"logs": list_audit_logs(record_id=document_id)}
    return {"logs": list_audit_logs(actor_email=user["email"])}

@app.get("/dashboard/stats")
def dashboard_stats(user=Depends(get_current_user)):
    if user["role"] == "citizen":
        docs = list_documents_for_user(user["email"])
        return {"documents_processed":len(docs),"verified":sum(d.get("verification_status")=="approved" for d in docs),"pending_review":sum(d.get("verification_status") in {"pending","needs_review","request_correction"} for d in docs),"rejected":sum(d.get("verification_status")=="rejected" for d in docs),"discrepancies":sum(d.get("validation_status")=="discrepancy" for d in docs)}
    return get_stats()

@app.get("/dashboard/analytics")
def analytics(user=Depends(require_roles("admin"))):
    return get_analytics()

def duplicate_score(a,b):
    weights={"owner_name":.22,"survey_number":.35,"village":.10,"district":.08,"tehsil":.04,"area":.08,"document_number":.05,"khasra_number":.03,"khata_number":.03,"plot_number":.02}
    return round(sum(sim(a.get(k),b.get(k))*w for k,w in weights.items())*100,1)

@app.get("/duplicates")
def duplicates(user=Depends(require_roles("officer", "admin"))):
    records = list_records(); groups = []
    for i,a in enumerate(records):
        for b in records[i+1:]:
            score = duplicate_score(a,b)
            if a.get("survey_number") and a.get("survey_number") == b.get("survey_number") and score >= 70:
                groups.append({"score":score,"risk":"high" if score>=90 else "medium","reason":"Same survey number with closely matching land details","records":[a,b]})
    groups.sort(key=lambda x:x["score"], reverse=True)
    return {"groups":groups}

@app.get("/duplicates/{document_id}")
def document_duplicates(document_id, user=Depends(require_roles("officer", "admin"))):
    doc = get_document(document_id); role_check_doc(doc,user)
    fields = doc["extracted_fields"]; survey = fields.get("survey_number"); candidates=[]
    if survey:
        for r in find_records_by_survey_number(survey):
            candidates.append({"type":"official_record","score":duplicate_score(fields,r),"record":r})
    for other in list_documents_all():
        if other["document_id"] == document_id:
            continue
        s = duplicate_score(fields, other["extracted_fields"])
        if s >= 75:
            candidates.append({"type":"submitted_document","score":s,"document":other})
    candidates = sorted(candidates,key=lambda x:x["score"],reverse=True)[:10]
    add_audit(user["email"],user["role"],"DUPLICATE_SCAN",document_id,json.dumps({"count":len(candidates)}))
    return {"candidates":candidates,"possible_duplicate":any(x["score"]>=85 for x in candidates)}

@app.get("/gis/parcels")
def gis_list(user=Depends(get_current_user)):
    return {"parcels":get_parcels()}

@app.get("/gis/parcels/{survey_number:path}")
def gis_one(survey_number,user=Depends(get_current_user)):
    p=get_parcel(survey_number); return {"found":bool(p),"parcel":p} if p else {"found":False,"message":"No parcel found"}

@app.get("/gis/compare/{document_id}")
def gis_compare(document_id,user=Depends(get_current_user)):
    doc=get_document(document_id); role_check_doc(doc,user); survey=doc["extracted_fields"].get("survey_number"); p=get_parcel(survey) if survey else None
    return {"document_id":document_id,"survey_number":survey,"parcel":p,"area_match":bool(p and norm(doc["extracted_fields"].get("area"))==norm(p.get("area")))}

@app.post("/gis/import")
async def gis_import(file:UploadFile=File(...),user=Depends(require_roles("admin"))):
    if not (file.filename or "").lower().endswith(".geojson"):
        raise HTTPException(400,"Upload a .geojson file")
    try:
        payload=json.loads((await file.read()).decode("utf-8")); count=0
    except Exception as exc:
        raise HTTPException(400,f"Invalid GeoJSON: {exc}")
    features=payload.get("features",[]) if payload.get("type")=="FeatureCollection" else []
    for f in features:
        prop=f.get("properties",{}); survey=prop.get("survey_number") or prop.get("survey")
        if not survey: continue
        center=prop.get("center",[0,0])
        upsert_parcel({"survey_number":survey,"parcel_id":prop.get("parcel_id"),"village":prop.get("village"),"district":prop.get("district"),"area":prop.get("area"),"center":center,"geometry":f.get("geometry",{})},"Imported GeoJSON"); count+=1
    add_audit(user["email"],user["role"],"GIS_IMPORT","",f"Imported {count} parcels")
    return {"success":True,"imported":count}

@app.get("/integrations/status")
def integrations(user=Depends(require_roles("officer", "admin"))):
    return {"integrations":integration_status()}

@app.get("/integrations/logs")
def integration_logs(document_id:str|None=None,user=Depends(require_roles("officer", "admin"))):
    return {"logs":list_integration_logs(document_id)}

@app.post("/integrations/lrms/sync/{document_id}")
def integration_lrms(document_id,user=Depends(require_roles("officer", "admin"))):
    doc=get_document(document_id); role_check_doc(doc,user); rec=find_record_by_survey_number(doc.get("survey_number") or "")
    if not rec: raise HTTPException(400,"No official record available")
    result=lrms_sync(rec,doc); add_integration_log(document_id,user["email"],user["role"],"LRMS","SYNC",result["status"],json.dumps(result)); add_audit(user["email"],user["role"],"LRMS_SYNC",document_id,result["status"]); return result

@app.post("/integrations/dilrmp/export/{document_id}")
def integration_dilrmp(document_id,user=Depends(require_roles("officer", "admin"))):
    doc=get_document(document_id); role_check_doc(doc,user); rec=find_record_by_survey_number(doc.get("survey_number") or "")
    if not rec: raise HTTPException(400,"No official record available")
    result=dilrmp_export(rec,doc); add_integration_log(document_id,user["email"],user["role"],"DILRMP","EXPORT",result["status"],json.dumps(result)); add_audit(user["email"],user["role"],"DILRMP_EXPORT",document_id,result["status"]); return result

@app.get("/admin/users")
def admin_users(user=Depends(require_roles("admin"))):
    return {"users":list_users()}

@app.post("/admin/users")
def admin_create_user(req:UserCreate,user=Depends(require_roles("admin"))):
    email=req.email.lower().strip()
    if req.role not in {"citizen","officer","admin"}: raise HTTPException(400,"Invalid role")
    if get_user(email): raise HTTPException(409,"User already exists")
    create_user(email,req.name.strip(),req.role,hash_password(req.password)); add_audit(user["email"],user["role"],"USER_CREATED",email,f"Created {req.role} user")
    return {"success":True,"user":{"email":email,"name":req.name.strip(),"role":req.role}}

@app.get("/admin/system-export")
def system_export(user=Depends(require_roles("admin"))):
    return {"records":list_records(),"documents":[{k:v for k,v in d.items() if k not in {"raw_text"}} for d in list_documents_all()],"analytics":get_analytics(),"audit":list_audit_logs()[:100],"integrations":list_integration_logs()[:100],"export_generated_at":now()}
