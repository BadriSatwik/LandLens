from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent
DB = BASE / "landverify.db"
STORAGE_DIR = BASE / "storage" / "documents"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

OFFICIAL_ROWS = [
    ("LR-0001", "Ramesh Kumar", "145/2", "Kamareddy", "Nizamabad", "Telangana", "Kamareddy", "K-145-2", "KH-7788", "P-1452", "2.5 acres", "Agricultural", "Individual", "Updated", "DOC-2026-1452", "14 August 2026", "Verified", "Officer Demo", "Baseline official record"),
    ("LR-0002", "Suresh Reddy", "146/1", "Kamareddy", "Nizamabad", "Telangana", "Kamareddy", "K-146-1", "KH-7789", "P-1461", "3.0 acres", "Agricultural", "Individual", "Updated", "DOC-2026-1461", "18 August 2026", "Verified", "Officer Demo", "All fields matched"),
    ("LR-0003", "Anil Kumar", "147/3", "Banswada", "Kamareddy", "Telangana", "Banswada", "K-147-3", "KH-7790", "P-1473", "1.75 acres", "Agricultural", "Joint", "Pending", "DOC-2026-1473", "20 August 2026", "Pending Review", "—", "Awaiting officer verification"),
    ("LR-0004", "Lakshmi Devi", "148/2", "Bichkunda", "Kamareddy", "Telangana", "Bichkunda", "K-148-2", "KH-7791", "P-1482", "4.2 acres", "Residential", "Individual", "Updated", "DOC-2026-1482", "22 August 2026", "Verified", "Officer Demo", "Verified against existing record"),
    ("LR-0005", "Mohammed Imran", "149/5", "Yellareddy", "Kamareddy", "Telangana", "Yellareddy", "K-149-5", "KH-7792", "P-1495", "2.0 acres", "Commercial", "Individual", "Disputed", "DOC-2026-1495", "25 August 2026", "Discrepancy", "Officer Demo", "Owner name mismatch detected"),
    ("LR-0006", "Priya Sharma", "150/1", "Kamareddy", "Nizamabad", "Telangana", "Kamareddy", "K-150-1", "KH-7793", "P-1501", "5.0 acres", "Agricultural", "Individual", "Updated", "DOC-2026-1501", "27 August 2026", "Verified", "Officer Demo", "All required fields matched"),
    ("LR-0007", "Vijay Kumar", "151/4", "Domakonda", "Kamareddy", "Telangana", "Domakonda", "K-151-4", "KH-7794", "P-1514", "2.25 acres", "Agricultural", "Individual", "Pending", "DOC-2026-1514", "29 August 2026", "Needs Review", "—", "Low OCR confidence"),
    ("LR-0008", "Geetha Rani", "152/2", "Bibipet", "Kamareddy", "Telangana", "Bibipet", "K-152-2", "KH-7795", "P-1522", "3.5 acres", "Agricultural", "Individual", "Updated", "DOC-2026-1522", "30 August 2026", "Verified", "Officer Demo", "Validated successfully"),
    ("LR-0009", "Ramesh Kumar", "145/2", "Kamareddy", "Nizamabad", "Telangana", "Kamareddy", "K-145-2", "KH-7788", "P-1452", "2.5 acres", "Agricultural", "Individual", "Updated", "DOC-2026-1452-COPY", "14 August 2026", "Possible Duplicate", "—", "Same survey/owner/area as LR-0001"),
    ("LR-0010", "Ravi Kumar", "145/2", "Kamareddy", "Nizamabad", "Telangana", "Kamareddy", "K-145-2", "KH-7788", "P-1452", "2.5 acres", "Agricultural", "Individual", "Updated", "DOC-2026-1452", "14 August 2026", "Discrepancy", "—", "Demo: uploaded owner differs from official owner"),
]

RECORD_COLUMNS = ["record_id","owner_name","survey_number","village","district","state","tehsil","khasra_number","khata_number","plot_number","area","land_classification","ownership_type","mutation_status","document_number","registration_date","status","last_verified_by","remarks"]


def connect():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def now():
    return datetime.now(timezone.utc).isoformat()


def initialize_database():
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS records(
            record_id TEXT PRIMARY KEY, owner_name TEXT, survey_number TEXT, village TEXT,
            district TEXT, state TEXT, tehsil TEXT, khasra_number TEXT, khata_number TEXT,
            plot_number TEXT, area TEXT, land_classification TEXT, ownership_type TEXT,
            mutation_status TEXT, document_number TEXT, registration_date TEXT, status TEXT,
            last_verified_by TEXT, remarks TEXT
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS documents(
            document_id TEXT PRIMARY KEY, original_filename TEXT NOT NULL, stored_path TEXT NOT NULL,
            mime_type TEXT NOT NULL, file_size INTEGER NOT NULL, uploaded_by TEXT NOT NULL,
            uploaded_role TEXT NOT NULL, uploaded_at TEXT NOT NULL, processing_status TEXT NOT NULL,
            language_code TEXT, language_status TEXT, ocr_mode TEXT, recognition_note TEXT,
            extracted_fields TEXT, confidence TEXT, raw_text TEXT, survey_number TEXT,
            validation_score REAL, validation_status TEXT, validation_details TEXT,
            verification_status TEXT NOT NULL DEFAULT 'pending', verification_remarks TEXT,
            verified_by TEXT, verified_at TEXT
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS audit_logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT, actor_email TEXT NOT NULL, actor_role TEXT NOT NULL,
            action TEXT NOT NULL, record_id TEXT, details TEXT, created_at TEXT NOT NULL
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS feedback(
            id INTEGER PRIMARY KEY AUTOINCREMENT, document_id TEXT NOT NULL, actor_email TEXT NOT NULL,
            actor_role TEXT NOT NULL, field_name TEXT NOT NULL, original_value TEXT,
            corrected_value TEXT NOT NULL, confidence_before REAL, notes TEXT, created_at TEXT NOT NULL
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS integration_logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT, document_id TEXT, actor_email TEXT NOT NULL,
            actor_role TEXT NOT NULL, integration_name TEXT NOT NULL, action TEXT NOT NULL,
            status TEXT NOT NULL, details TEXT, created_at TEXT NOT NULL
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS gis_parcels(
            survey_number TEXT PRIMARY KEY, parcel_id TEXT NOT NULL, village TEXT, district TEXT,
            area TEXT, center_lon REAL, center_lat REAL, geometry_json TEXT NOT NULL, source TEXT NOT NULL
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS users(
            email TEXT PRIMARY KEY, name TEXT NOT NULL, role TEXT NOT NULL,
            password_hash TEXT NOT NULL, created_at TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1
        )""")
        # Upgrade older local databases in place.
        rec_cols = {r[1] for r in con.execute("PRAGMA table_info(records)").fetchall()}
        for name in ["state","tehsil","khasra_number","khata_number","plot_number","land_classification","ownership_type","mutation_status"]:
            if name not in rec_cols:
                con.execute(f"ALTER TABLE records ADD COLUMN {name} TEXT")
        count = con.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        if count == 0:
            placeholders=",".join("?" for _ in RECORD_COLUMNS)
            con.executemany(f"INSERT INTO records({','.join(RECORD_COLUMNS)}) VALUES ({placeholders})", OFFICIAL_ROWS)
        if con.execute("SELECT COUNT(*) FROM gis_parcels").fetchone()[0] == 0:
            parcels=[
                ("145/2","PARCEL-145-2","Kamareddy","Nizamabad","2.5 acres",78.3374,18.3215,[[[78.3358,18.3204],[78.3390,18.3204],[78.3396,18.3226],[78.3370,18.3234],[78.3358,18.3204]]],"LandVerify demo cadastral layer"),
                ("146/1","PARCEL-146-1","Kamareddy","Nizamabad","3.0 acres",78.3420,18.3240,[[[78.3403,18.3228],[78.3438,18.3228],[78.3440,18.3253],[78.3412,18.3255],[78.3403,18.3228]]],"LandVerify demo cadastral layer"),
                ("147/3","PARCEL-147-3","Banswada","Kamareddy","1.75 acres",77.8830,18.3780,[[[77.8814,18.3768],[77.8841,18.3768],[77.8847,18.3792],[77.8820,18.3796],[77.8814,18.3768]]],"LandVerify demo cadastral layer"),
                ("149/5","PARCEL-149-5","Yellareddy","Kamareddy","2.0 acres",78.3920,18.1840,[[[78.3903,18.1828],[78.3937,18.1828],[78.3940,18.1853],[78.3910,18.1857],[78.3903,18.1828]]],"LandVerify demo cadastral layer"),
            ]
            con.executemany("INSERT INTO gis_parcels(survey_number,parcel_id,village,district,area,center_lon,center_lat,geometry_json,source) VALUES (?,?,?,?,?,?,?,?,?)", [(a,b,c,d,e,f,g,json.dumps({"type":"Polygon","coordinates":h}),i) for a,b,c,d,e,f,g,h,i in parcels])
        con.commit()


def _json(value, default=None):
    try:return json.loads(value) if value else default
    except Exception:return default


def _doc(row):
    d=dict(row)
    for key in ("extracted_fields","confidence","validation_details"):d[key]=_json(d.get(key),{})
    return d


def list_records():
    with connect() as con:return [dict(r) for r in con.execute("SELECT * FROM records ORDER BY record_id")]

def find_record_by_survey_number(survey):
    with connect() as con:r=con.execute("SELECT * FROM records WHERE survey_number=? ORDER BY record_id LIMIT 1",(survey,)).fetchone()
    return dict(r) if r else None

def find_records_by_survey_number(survey):
    with connect() as con:rows=con.execute("SELECT * FROM records WHERE survey_number=? ORDER BY record_id",(survey,)).fetchall()
    return [dict(r) for r in rows]

def insert_document(document_id, **kw):
    cols=["document_id","original_filename","stored_path","mime_type","file_size","uploaded_by","uploaded_role","uploaded_at","processing_status","language_code","language_status","ocr_mode","recognition_note","extracted_fields","confidence","raw_text","survey_number"]
    vals=[document_id,kw["original_filename"],kw["stored_path"],kw["mime_type"],kw["file_size"],kw["uploaded_by"],kw["uploaded_role"],now(),"extracted",kw.get("language_code"),kw.get("language_status"),kw.get("ocr_mode"),kw.get("recognition_note"),json.dumps(kw.get("extracted_fields",{})),json.dumps(kw.get("confidence",{})),kw.get("raw_text", ""),kw.get("survey_number")]
    with connect() as con:con.execute(f"INSERT INTO documents({','.join(cols)}) VALUES ({','.join('?'*len(cols))})",vals);con.commit()

def get_document(document_id):
    with connect() as con:r=con.execute("SELECT * FROM documents WHERE document_id=?",(document_id,)).fetchone()
    return _doc(r) if r else None

def list_documents_all():
    with connect() as con:rows=con.execute("SELECT * FROM documents ORDER BY uploaded_at DESC").fetchall()
    return [_doc(r) for r in rows]

def list_documents_for_user(email):
    with connect() as con:rows=con.execute("SELECT * FROM documents WHERE uploaded_by=? ORDER BY uploaded_at DESC",(email,)).fetchall()
    return [_doc(r) for r in rows]

def update_validation(document_id, score, status, details):
    with connect() as con:con.execute("UPDATE documents SET validation_score=?,validation_status=?,validation_details=? WHERE document_id=?",(score,status,json.dumps(details),document_id));con.commit()

def update_extracted_fields(document_id, fields):
    with connect() as con:con.execute("UPDATE documents SET extracted_fields=?,survey_number=? WHERE document_id=?",(json.dumps(fields),fields.get("survey_number"),document_id));con.commit()

def update_verification(document_id,status,remarks,verified_by):
    with connect() as con:con.execute("UPDATE documents SET verification_status=?,verification_remarks=?,verified_by=?,verified_at=? WHERE document_id=?",(status,remarks,verified_by,now(),document_id));con.commit()

def list_verification_queue():
    with connect() as con:rows=con.execute("SELECT * FROM documents WHERE verification_status IN ('pending','needs_review','request_correction') AND (validation_status IS NULL OR validation_status IN ('discrepancy','warning','not_found')) ORDER BY uploaded_at DESC").fetchall()
    return [_doc(r) for r in rows]

def get_stats():
    docs=list_documents_all()
    return {"documents_processed":len(docs),"verified":sum(d.get("verification_status")=="approved" for d in docs),"pending_review":sum(d.get("verification_status") in {"pending","needs_review","request_correction"} for d in docs),"rejected":sum(d.get("verification_status")=="rejected" for d in docs),"discrepancies":sum(d.get("validation_status")=="discrepancy" for d in docs),"warnings":sum(d.get("validation_status")=="warning" for d in docs),"not_found":sum(d.get("validation_status")=="not_found" for d in docs),"review_queue":len(list_verification_queue())}

def add_audit(actor_email,actor_role,action,record_id="",details=""):
    with connect() as con:con.execute("INSERT INTO audit_logs(actor_email,actor_role,action,record_id,details,created_at) VALUES (?,?,?,?,?,?)",(actor_email,actor_role,action,record_id,details,now()));con.commit()

def list_audit_logs(actor_email=None,record_id=None,limit=500):
    q="SELECT * FROM audit_logs WHERE 1=1";p=[]
    if actor_email:q+=" AND actor_email=?";p.append(actor_email)
    if record_id:q+=" AND record_id=?";p.append(record_id)
    q+=" ORDER BY id DESC LIMIT ?";p.append(limit)
    with connect() as con:rows=con.execute(q,p).fetchall()
    return [dict(r) for r in rows]

def add_feedback(document_id,actor_email,actor_role,field_name,original_value,corrected_value,confidence_before,notes):
    with connect() as con:con.execute("INSERT INTO feedback(document_id,actor_email,actor_role,field_name,original_value,corrected_value,confidence_before,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?)",(document_id,actor_email,actor_role,field_name,original_value,corrected_value,confidence_before,notes,now()));con.commit()

def list_feedback(document_id=None):
    q="SELECT * FROM feedback";p=[]
    if document_id:q+=" WHERE document_id=?";p.append(document_id)
    q+=" ORDER BY id DESC"
    with connect() as con:rows=con.execute(q,p).fetchall()
    return [dict(r) for r in rows]

def list_feedback_summary():
    with connect() as con:rows=con.execute("SELECT field_name,COUNT(*) AS count FROM feedback GROUP BY field_name ORDER BY count DESC").fetchall()
    return [dict(r) for r in rows]

def add_integration_log(document_id,actor_email,actor_role,integration_name,action,status,details=""):
    with connect() as con:con.execute("INSERT INTO integration_logs(document_id,actor_email,actor_role,integration_name,action,status,details,created_at) VALUES (?,?,?,?,?,?,?,?)",(document_id,actor_email,actor_role,integration_name,action,status,details,now()));con.commit()

def list_integration_logs(document_id=None):
    q="SELECT * FROM integration_logs";p=[]
    if document_id:q+=" WHERE document_id=?";p.append(document_id)
    q+=" ORDER BY id DESC"
    with connect() as con:rows=con.execute(q,p).fetchall()
    return [dict(r) for r in rows]

def get_analytics():
    docs=list_documents_all(); stats=get_stats(); validation={};verification={};errors={}; confs=[];low=0
    for d in docs:
        vs=d.get("validation_status") or "not_validated"; validation[vs]=validation.get(vs,0)+1
        ver=d.get("verification_status") or "pending"; verification[ver]=verification.get(ver,0)+1
        for v in d.get("confidence",{}).values():
            if isinstance(v,(int,float)) and v>0:confs.append(float(v));low+=int(v<70)
        for f,c in d.get("validation_details",{}).items():
            if isinstance(c,dict) and c.get("status")=="fail":errors[f]=errors.get(f,0)+1
    district={}; state={}
    for r in list_records():
        ds=r.get("district") or "Unknown"; st=r.get("state") or "Unknown"
        district.setdefault(ds,{"total":0,"verified":0,"attention":0});district[ds]["total"]+=1;district[ds]["verified"]+=int(str(r.get("status")).lower()=="verified");district[ds]["attention"]+=int(str(r.get("status")).lower()!="verified")
        state.setdefault(st,{"total":0,"verified":0,"attention":0});state[st]["total"]+=1;state[st]["verified"]+=int(str(r.get("status")).lower()=="verified");state[st]["attention"]+=int(str(r.get("status")).lower()!="verified")
    return {"summary":stats,"verification_status":verification,"validation_status":validation,"field_errors":errors,"low_confidence_fields":low,"average_confidence":round(sum(confs)/len(confs),1) if confs else 0.0,"district_progress":district,"state_progress":state,"learning_feedback":list_feedback_summary(),"documents_total":len(docs),"high_confidence_rate":round(sum(v>=90 for v in confs)/len(confs)*100,1) if confs else 0.0}

def get_parcels():
    with connect() as con:rows=con.execute("SELECT * FROM gis_parcels ORDER BY survey_number").fetchall()
    out=[]
    for r in rows:
        d=dict(r);d["center"]=[d.pop("center_lon"),d.pop("center_lat")];d["geometry"]=_json(d.pop("geometry_json"),{});out.append(d)
    return out

def get_parcel(survey):
    with connect() as con:r=con.execute("SELECT * FROM gis_parcels WHERE survey_number=?",(survey,)).fetchone()
    if not r:return None
    d=dict(r);d["center"]=[d.pop("center_lon"),d.pop("center_lat")];d["geometry"]=_json(d.pop("geometry_json"),{});return d

def upsert_parcel(parcel,source):
    center=parcel.get("center") or [0,0]
    with connect() as con:con.execute("INSERT INTO gis_parcels(survey_number,parcel_id,village,district,area,center_lon,center_lat,geometry_json,source) VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(survey_number) DO UPDATE SET parcel_id=excluded.parcel_id,village=excluded.village,district=excluded.district,area=excluded.area,center_lon=excluded.center_lon,center_lat=excluded.center_lat,geometry_json=excluded.geometry_json,source=excluded.source",(parcel["survey_number"],parcel.get("parcel_id") or f"PARCEL-{parcel['survey_number'].replace('/','-')}",parcel.get("village"),parcel.get("district"),parcel.get("area"),center[0],center[1],json.dumps(parcel.get("geometry",{})),source));con.commit()

def create_user(email,name,role,password_hash):
    with connect() as con:con.execute("INSERT INTO users(email,name,role,password_hash,created_at,active) VALUES (?,?,?,?,?,1)",(email.lower().strip(),name,role,password_hash,now()));con.commit()

def get_user(email):
    with connect() as con:r=con.execute("SELECT * FROM users WHERE email=? AND active=1",(email.lower().strip(),)).fetchone()
    return dict(r) if r else None

def list_users():
    with connect() as con:rows=con.execute("SELECT email,name,role,created_at,active FROM users ORDER BY created_at").fetchall()
    return [dict(r) for r in rows]


def seed_demo_documents():
    sample = BASE.parent / "sample_data" / "demo_land_record.png"
    if not sample.exists():
        return
    with connect() as con:
        count = con.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        if count:
            return
        demos = [
            {
                "document_id":"LV-DEMO-001","original_filename":"demo_land_record.png","stored_path":str(sample),"mime_type":"image/png","file_size":sample.stat().st_size,
                "uploaded_by":"citizen@landverify.demo","uploaded_role":"citizen","language_code":"en","language_status":"English OCR","ocr_mode":"land_record","recognition_note":"Demo seeded record for the hackathon flow",
                "fields":{"owner_name":"Ravi Kumar","survey_number":"145/2","village":"Kamareddy","district":None,"tehsil":None,"khasra_number":None,"khata_number":None,"plot_number":None,"area":"2.5 acres","land_classification":None,"ownership_type":None,"mutation_status":None,"document_number":"DOC-2026-1452","registration_date":None},
                "confidence":{"owner_name":98.0,"survey_number":99.0,"village":98.0,"district":0.0,"tehsil":0.0,"khasra_number":0.0,"khata_number":0.0,"plot_number":0.0,"area":97.0,"land_classification":0.0,"ownership_type":0.0,"mutation_status":0.0,"document_number":96.0,"registration_date":0.0},
                "validation_score":80,"validation_status":"discrepancy","validation_details":{"owner_name":{"status":"fail","message":"Uploaded record says Ravi Kumar, existing record says Ramesh Kumar"},"survey_number":{"status":"pass","message":"Survey number matches the existing record"},"village":{"status":"pass","message":"Village matches the existing record"},"area":{"status":"pass","message":"Land area matches the existing record"}},"verification_status":"pending"
            },
            {
                "document_id":"LV-DEMO-002","original_filename":"demo_land_record_review.png","stored_path":str(sample),"mime_type":"image/png","file_size":sample.stat().st_size,
                "uploaded_by":"officer@landverify.demo","uploaded_role":"officer","language_code":"en","language_status":"English OCR","ocr_mode":"land_record","recognition_note":"Demo low-confidence review case",
                "fields":{"owner_name":"Vijay Kumar","survey_number":"151/4","village":"Domakonda","district":"Kamareddy","tehsil":"Domakonda","khasra_number":"K-151-4","khata_number":"KH-7794","plot_number":"P-1514","area":"2.25 acres","land_classification":"Agricultural","ownership_type":"Individual","mutation_status":"Pending","document_number":"DOC-2026-1514","registration_date":"29 August 2026"},
                "confidence":{"owner_name":61.0,"survey_number":83.0,"village":76.0,"district":58.0,"tehsil":56.0,"khasra_number":49.0,"khata_number":44.0,"plot_number":47.0,"area":71.0,"land_classification":68.0,"ownership_type":72.0,"mutation_status":55.0,"document_number":66.0,"registration_date":52.0},
                "validation_score":71,"validation_status":"warning","validation_details":{"owner_name":{"status":"review","message":"Owner name is very similar; review for OCR noise"}},"verification_status":"needs_review"
            },
            {
                "document_id":"LV-DEMO-003","original_filename":"demo_verified_record.png","stored_path":str(sample),"mime_type":"image/png","file_size":sample.stat().st_size,
                "uploaded_by":"officer@landverify.demo","uploaded_role":"officer","language_code":"en","language_status":"English OCR","ocr_mode":"land_record","recognition_note":"Demo verified record",
                "fields":{"owner_name":"Suresh Reddy","survey_number":"146/1","village":"Kamareddy","district":"Nizamabad","tehsil":"Kamareddy","khasra_number":"K-146-1","khata_number":"KH-7789","plot_number":"P-1461","area":"3.0 acres","land_classification":"Agricultural","ownership_type":"Individual","mutation_status":"Updated","document_number":"DOC-2026-1461","registration_date":"18 August 2026"},
                "confidence":{"owner_name":96.0,"survey_number":99.0,"village":96.0,"district":94.0,"tehsil":93.0,"khasra_number":95.0,"khata_number":95.0,"plot_number":95.0,"area":97.0,"land_classification":92.0,"ownership_type":94.0,"mutation_status":93.0,"document_number":97.0,"registration_date":91.0},
                "validation_score":100,"validation_status":"valid","validation_details":{},"verification_status":"approved","verified_by":"officer@landverify.demo","verification_remarks":"Demo verified record"
            },
        ]
        for d in demos:
            con.execute("INSERT INTO documents(document_id,original_filename,stored_path,mime_type,file_size,uploaded_by,uploaded_role,uploaded_at,processing_status,language_code,language_status,ocr_mode,recognition_note,extracted_fields,confidence,raw_text,survey_number,validation_score,validation_status,validation_details,verification_status,verification_remarks,verified_by,verified_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (d["document_id"],d["original_filename"],d["stored_path"],d["mime_type"],d["file_size"],d["uploaded_by"],d["uploaded_role"],now(),"extracted",d["language_code"],d["language_status"],d["ocr_mode"],d["recognition_note"],json.dumps(d["fields"]),json.dumps(d["confidence"]),"Demo seeded land record",d["fields"].get("survey_number"),d["validation_score"],d["validation_status"],json.dumps(d["validation_details"]),d["verification_status"],d.get("verification_remarks"),d.get("verified_by"),now() if d.get("verified_by") else None))
        con.commit()
