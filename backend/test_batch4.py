from pathlib import Path
import io
import json
import os
import tempfile

from PIL import Image, ImageDraw, ImageFont
import pymupdf
from fastapi.testclient import TestClient

# Make package-local import work.
import main


# Make the regression suite repeatable by starting from a clean local state.
for _path in (main.DB, main.STORAGE_DIR):
    if isinstance(_path, Path) and _path.is_file():
        _path.unlink(missing_ok=True)
    elif isinstance(_path, Path) and _path.is_dir():
        import shutil
        shutil.rmtree(_path, ignore_errors=True)
        _path.mkdir(parents=True, exist_ok=True)
main.initialize_database()
main.seed_demo_users()


def make_test_image(path: Path):
    img = Image.new("RGB", (1600, 900), "white")
    draw = ImageDraw.Draw(img)
    lines = [
        "Government of Telangana",
        "PROPERTY REGISTER",
        "Owner Name: Ravi Kumar",
        "Survey No: 145/2",
        "Village: Kamareddy",
        "District: Nizamabad",
        "Tehsil: Kamareddy",
        "Khasra Number: K-145-2",
        "Khata Number: KH-7788",
        "Plot Number: P-1452",
        "Area: 2.5 acres",
        "Land Classification: Agricultural",
        "Ownership Type: Individual",
        "Mutation Status: Updated",
        "Document No: DOC-2026-1452",
        "Registration Date: 14 August 2026",
    ]
    y = 60
    for line in lines:
        draw.text((80, y), line, fill="black")
        y += 48
    img.save(path)


def make_test_pdf(path: Path):
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    text = """Government of Telangana\nPROPERTY REGISTER\nOwner Name: Ravi Kumar\nSurvey No: 145/2\nVillage: Kamareddy\nDistrict: Nizamabad\nArea: 2.5 acres\nDocument No: DOC-2026-1452\nRegistration Date: 14 August 2026"""
    page.insert_text((55, 65), text, fontsize=13)
    doc.save(path)
    doc.close()


with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    img_path = Path("/mnt/data/batch2_test_land.png")
    pdf_path = td / "land.pdf"
    make_test_pdf(pdf_path)

    with TestClient(main.app) as client:
        # health
        r = client.get("/health")
        assert r.status_code == 200 and r.json()["status"] == "healthy"

        # Public API docs and authenticated endpoint catalog.
        assert client.get("/docs").status_code == 200

        tokens = {}
        for email, password, role in [
            ("citizen@landverify.demo", "citizen123", "citizen"),
            ("officer@landverify.demo", "officer123", "officer"),
            ("admin@landverify.demo", "admin123", "admin"),
        ]:
            r = client.post("/login", data={"username": email, "password": password})
            assert r.status_code == 200, r.text
            data = r.json(); assert data["user"]["role"] == role
            tokens[role] = data["access_token"]

        # Citizen cannot access officer/admin endpoints.
        r = client.get("/records", headers={"Authorization": f"Bearer {tokens['citizen']}"})
        assert r.status_code == 403
        r = client.get("/admin/users", headers={"Authorization": f"Bearer {tokens['citizen']}"})
        assert r.status_code == 403

        # Admin can access user management.
        r = client.get("/admin/users", headers={"Authorization": f"Bearer {tokens['admin']}"})
        assert r.status_code == 200

        # Admin can create a persistent user; login with the new account.
        new_email = "reviewer@landverify.demo"
        r = client.post("/admin/users", headers={"Authorization": f"Bearer {tokens['admin']}"}, json={"email": new_email, "name": "Reviewer Demo", "role": "officer", "password": "reviewer123"})
        assert r.status_code in (200, 409), r.text
        r = client.post("/login", data={"username": new_email, "password": "reviewer123"})
        assert r.status_code == 200, r.text

        # Live sample image: field-aware land-record mode should recover the demo values.
        sample = Path(__file__).resolve().parent.parent / "sample_data" / "demo_land_record.png"
        with open(sample, "rb") as f:
            r = client.post("/extract", headers={"Authorization": f"Bearer {tokens['citizen']}"}, files={"file": ("demo_land_record.png", f, "image/png")}, data={"language": "en", "mode": "land_record"})
        assert r.status_code == 200, r.text
        sample_data = r.json()["fields"]
        assert sample_data["owner_name"] == "Ravi Kumar"
        assert sample_data["survey_number"] == "145/2"
        assert sample_data["village"] == "Kamareddy"
        assert sample_data["area"] == "2.5 acres"
        assert sample_data["document_number"] == "DOC-2026-1452"

        # Image extract with advanced fields.
        with open(img_path, "rb") as f:
            r = client.post("/extract", headers={"Authorization": f"Bearer {tokens['citizen']}"}, files={"file": ("land.png", f, "image/png")}, data={"language": "en", "mode": "land_record"})
        assert r.status_code == 200, r.text
        image_data = r.json()
        assert image_data["success"] is True
        assert image_data["fields"]["survey_number"] == "145/2"
        assert image_data["fields"]["owner_name"] == "Ravi Kumar"
        assert image_data["fields"]["district"] == "Nizamabad"
        doc_id = image_data["document_id"]

        # Authenticated document download.
        r = client.get(f"/documents/{doc_id}/download", headers={"Authorization": f"Bearer {tokens['citizen']}"})
        assert r.status_code == 200

        # Handwriting mode should execute the dedicated preprocessing path.
        with open(img_path, "rb") as f:
            r = client.post("/extract", headers={"Authorization": f"Bearer {tokens['citizen']}"}, files={"file": ("handwritten.png", f, "image/png")}, data={"language": "en", "mode": "handwritten"})
        assert r.status_code == 200
        assert "handwriting" in r.json()["recognition_note"].lower()

        # Language fallback must not crash when a requested pack is available/unavailable.
        with open(img_path, "rb") as f:
            r = client.post("/extract", headers={"Authorization": f"Bearer {tokens['citizen']}"}, files={"file": ("telugu-request.png", f, "image/png")}, data={"language": "te", "mode": "printed"})
        assert r.status_code == 200

        # PDF extract.
        with open(pdf_path, "rb") as f:
            r = client.post("/extract", headers={"Authorization": f"Bearer {tokens['officer']}"}, files={"file": ("land.pdf", f, "application/pdf")}, data={"language": "en", "mode": "printed"})
        assert r.status_code == 200, r.text
        pdf_data = r.json()
        assert pdf_data["fields"]["survey_number"] == "145/2"

        # Validate known discrepancy: Ravi vs official Ramesh.
        r = client.post(f"/validate?document_id={doc_id}", headers={"Authorization": f"Bearer {tokens['citizen']}"}, json=image_data["fields"])
        assert r.status_code == 200, r.text
        val = r.json(); assert val["status"] == "discrepancy"
        assert val["checks"]["owner_name"]["status"] == "fail"
        assert val["checks"]["survey_number"]["status"] == "pass"

        # Officer queue should contain document.
        r = client.get("/verification/queue", headers={"Authorization": f"Bearer {tokens['officer']}"})
        assert r.status_code == 200
        assert any(d["document_id"] == doc_id for d in r.json()["documents"])

        # Duplicate scan.
        r = client.get(f"/duplicates/{doc_id}", headers={"Authorization": f"Bearer {tokens['officer']}"})
        assert r.status_code == 200

        # Learning feedback.
        r = client.post("/learning/feedback", headers={"Authorization": f"Bearer {tokens['officer']}"}, json={"document_id": doc_id, "field_name": "owner_name", "corrected_value": "Ramesh Kumar", "notes": "Demo correction"})
        assert r.status_code == 200

        # Verification decision.
        r = client.post(f"/verification/{doc_id}", headers={"Authorization": f"Bearer {tokens['officer']}"}, json={"status":"approved","remarks":"Approved after review"})
        assert r.status_code == 200
        r = client.get("/verification/queue", headers={"Authorization": f"Bearer {tokens['officer']}"})
        assert r.status_code == 200
        assert not any(d["document_id"] == doc_id for d in r.json()["documents"])

        # Endpoint catalog is live and complete enough for the application UI.
        r = client.get("/api/endpoints", headers={"Authorization": f"Bearer {tokens["officer"]}"})
        assert r.status_code == 200 and any(x["path"] == "/validate" for x in r.json()["endpoints"])

        # Citizen cannot approve.
        r = client.post(f"/verification/{doc_id}", headers={"Authorization": f"Bearer {tokens['citizen']}"}, json={"status":"approved","remarks":"No"})
        assert r.status_code == 403

        # Audit and analytics.
        assert client.get("/audit", headers={"Authorization": f"Bearer {tokens['admin']}"}).status_code == 200
        assert client.get("/dashboard/analytics", headers={"Authorization": f"Bearer {tokens['admin']}"}).status_code == 200

        # GIS.
        assert client.get("/gis/parcels", headers={"Authorization": f"Bearer {tokens['officer']}"}).status_code == 200
        assert client.get("/gis/parcels/145/2", headers={"Authorization": f"Bearer {tokens['officer']}"}).status_code == 200

        # Integrations.
        assert client.get("/integrations/status", headers={"Authorization": f"Bearer {tokens['officer']}"}).status_code == 200
        assert client.post(f"/integrations/lrms/sync/{doc_id}", headers={"Authorization": f"Bearer {tokens['officer']}"}).status_code == 200
        assert client.post(f"/integrations/dilrmp/export/{doc_id}", headers={"Authorization": f"Bearer {tokens['officer']}"}).status_code == 200

        # GeoJSON import permission and functionality.
        geojson = {"type":"FeatureCollection","features":[{"type":"Feature","properties":{"survey_number":"160/1","parcel_id":"P-160-1","village":"Kamareddy","district":"Nizamabad","area":"1.0 acres","center":[78.3,18.3]},"geometry":{"type":"Polygon","coordinates":[[[78.3,18.3],[78.31,18.3],[78.31,18.31],[78.3,18.31],[78.3,18.3]]]}}]}
        r = client.post("/gis/import", headers={"Authorization": f"Bearer {tokens['admin']}"}, files={"file":("parcel.geojson", io.BytesIO(json.dumps(geojson).encode()),"application/geo+json")})
        assert r.status_code == 200 and r.json()["imported"] == 1

print("BATCH 4 FULL BACKEND TESTS PASSED")
