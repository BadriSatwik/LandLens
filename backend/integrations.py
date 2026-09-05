from __future__ import annotations
import json, os
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def _stamp(): return datetime.now(timezone.utc).isoformat()


def _http_post(url: str, payload: dict) -> dict:
    data=json.dumps(payload).encode("utf-8")
    req=Request(url,data=data,headers={"Content-Type":"application/json","Accept":"application/json"},method="POST")
    try:
        with urlopen(req,timeout=5) as r:
            body=r.read().decode("utf-8")
            return {"status":"connected","http_status":r.status,"response":body[:2000]}
    except (HTTPError,URLError,OSError) as exc:
        return {"status":"error","message":str(exc)}


def _payload(record,document):
    return {"source":"LandVerify","document_id":document["document_id"],"survey_number":record.get("survey_number"),"owner_name":record.get("owner_name"),"village":record.get("village"),"district":record.get("district"),"tehsil":record.get("tehsil"),"khasra_number":record.get("khasra_number"),"khata_number":record.get("khata_number"),"plot_number":record.get("plot_number"),"area":record.get("area"),"land_classification":record.get("land_classification"),"ownership_type":record.get("ownership_type"),"mutation_status":record.get("mutation_status"),"document_number":record.get("document_number"),"registration_date":record.get("registration_date")}


def integration_status():
    return [
        {"name":"LRMS","mode":"live" if os.getenv("LANDVERIFY_LRMS_URL") else "mock","endpoint_configured":bool(os.getenv("LANDVERIFY_LRMS_URL")),"description":"Land Records Management System connector. Set LANDVERIFY_LRMS_URL for approved endpoint."},
        {"name":"DILRMP","mode":"live" if os.getenv("LANDVERIFY_DILRMP_URL") else "mock","endpoint_configured":bool(os.getenv("LANDVERIFY_DILRMP_URL")),"description":"DILRMP exchange connector. Set LANDVERIFY_DILRMP_URL for approved endpoint."},
        {"name":"GIS","mode":"local","endpoint_configured":True,"description":"GeoJSON cadastral service with import support for approved parcel datasets."},
        {"name":"Government APIs","mode":"adapter","endpoint_configured":bool(os.getenv("LANDVERIFY_GOV_API_URL")),"description":"Configurable authenticated REST integration boundary."},
    ]


def lrms_sync(record,document):
    payload=_payload(record,document); url=os.getenv("LANDVERIFY_LRMS_URL")
    result={"adapter":"LRMS","mode":"live" if url else "mock","status":"ready","timestamp":_stamp(),"payload":payload}
    if url: result["delivery"]=_http_post(url,payload); result["status"]=result["delivery"]["status"]
    return result


def dilrmp_export(record,document):
    payload=_payload(record,document); url=os.getenv("LANDVERIFY_DILRMP_URL")
    result={"adapter":"DILRMP","mode":"live" if url else "mock","status":"ready","timestamp":_stamp(),"format":"DILRMP-oriented JSON","payload":payload}
    if url: result["delivery"]=_http_post(url,payload); result["status"]=result["delivery"]["status"]
    return result
