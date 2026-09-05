from __future__ import annotations
import re
from typing import Iterable

LABELS = {
    "owner_name": [
        r"Owner\s*Name\s*[:\-]?\s*(.+?)(?:\n|$)",
        r"मालिक\s*(?:का\s*)?नाम\s*[:\-]?\s*(.+?)(?:\n|$)",
        r"(?:యజమాని|యజమాని\s*పేరు)\s*[:\-]?\s*(.+?)(?:\n|$)",
    ],
    "survey_number": [
        r"Survey\s*(?:No|Number)\s*[:\-]?\s*([0-9A-Za-z]+(?:\s*[/.-]\s*[0-9A-Za-z]+)*)",
        r"सर्वे\s*(?:नंबर|संख्या|क्र\.?)\s*[:\-]?\s*([0-9A-Za-z]+(?:\s*[/.-]\s*[0-9A-Za-z]+)*)",
        r"సర్వే\s*(?:నం|నంబర్|సంఖ్య)\s*[:\-]?\s*([0-9A-Za-z]+(?:\s*[/.-]\s*[0-9A-Za-z]+)*)",
    ],
    "khasra_number": [
        r"Khasra\s*(?:No|Number)\s*[:\-]?\s*([A-Za-z0-9/-]+)",
        r"खसरा\s*(?:नंबर|संख्या)\s*[:\-]?\s*([A-Za-z0-9/-]+)",
        r"ఖస్రా\s*(?:నం|నంబర్|సంఖ్య)\s*[:\-]?\s*([A-Za-z0-9/-]+)",
    ],
    "khata_number": [
        r"Khata\s*(?:No|Number)\s*[:\-]?\s*([A-Za-z0-9/-]+)",
        r"खाता\s*(?:नंबर|संख्या)\s*[:\-]?\s*([A-Za-z0-9/-]+)",
        r"ఖాతా\s*(?:నం|నంబర్|సంఖ్య)\s*[:\-]?\s*([A-Za-z0-9/-]+)",
    ],
    "plot_number": [
        r"Plot\s*(?:No|Number)\s*[:\-]?\s*([A-Za-z0-9/-]+)",
        r"प्लॉट\s*(?:नंबर|संख्या)\s*[:\-]?\s*([A-Za-z0-9/-]+)",
        r"ప్లాట్\s*(?:నం|నంబర్|సంఖ్య)\s*[:\-]?\s*([A-Za-z0-9/-]+)",
    ],
    "village": [
        r"Village\s*[:\-]?\s*(.+?)(?:\n|$)",
        r"ग्राम\s*[:\-]?\s*(.+?)(?:\n|$)",
        r"గ్రామం?\s*[:\-]?\s*(.+?)(?:\n|$)",
    ],
    "tehsil": [
        r"Tehsil\s*[:\-]?\s*(.+?)(?:\n|$)",
        r"तहसील\s*[:\-]?\s*(.+?)(?:\n|$)",
        r"తహసీల్\s*[:\-]?\s*(.+?)(?:\n|$)",
    ],
    "district": [
        r"District\s*[:\-]?\s*(.+?)(?:\n|$)",
        r"जिला\s*[:\-]?\s*(.+?)(?:\n|$)",
        r"జిల్లా\s*[:\-]?\s*(.+?)(?:\n|$)",
    ],
    "area": [
        r"Area\s*[:\-]?\s*([0-9]+(?:\s*[.,]\s*[0-9]+)?\s*(?:acres?|acre|hectares?|hectare|ha))",
        r"क्षेत्रफल\s*[:\-]?\s*([0-9]+(?:\s*[.,]\s*[0-9]+)?\s*(?:एकड़|हेक्टेयर|ha|hectares?))",
        r"విస్తీర్ణం\s*[:\-]?\s*([0-9]+(?:\s*[.,]\s*[0-9]+)?\s*(?:ఎకరాలు?|ఎకరం|acres?|acre|ha))",
    ],
    "land_classification": [
        r"Land\s*Classification\s*[:\-]?\s*(.+?)(?:\n|$)",
        r"भूमि\s*वर्गीकरण\s*[:\-]?\s*(.+?)(?:\n|$)",
        r"భూమి\s*వర్గీకరణ\s*[:\-]?\s*(.+?)(?:\n|$)",
    ],
    "ownership_type": [
        r"Ownership\s*Type\s*[:\-]?\s*(.+?)(?:\n|$)",
        r"स्वामित्व\s*प्रकार\s*[:\-]?\s*(.+?)(?:\n|$)",
        r"యాజమాన్యం\s*రకం\s*[:\-]?\s*(.+?)(?:\n|$)",
    ],
    "mutation_status": [
        r"Mutation\s*(?:Status)?\s*[:\-]?\s*(.+?)(?:\n|$)",
        r"म्यूटेशन\s*(?:स्थिति)?\s*[:\-]?\s*(.+?)(?:\n|$)",
        r"మ్యుటేషన్\s*(?:స్థితి)?\s*[:\-]?\s*(.+?)(?:\n|$)",
    ],
    "document_number": [
        r"Document\s*No\s*[:\-]?\s*([A-Za-z0-9/_-]+)",
        r"दस्तावेज़?\s*(?:संख्या|नंबर)\s*[:\-]?\s*([A-Za-z0-9/_-]+)",
        r"పత్రం\s*(?:నం|నంబర్|సంఖ్య)\s*[:\-]?\s*([A-Za-z0-9/_-]+)",
    ],
    "registration_date": [
        r"(?:Registration\s*Date|Registered\s*On)\s*[:\-]?\s*(.+?)(?:\n|$)",
        r"पंजीकरण\s*तिथि\s*[:\-]?\s*(.+?)(?:\n|$)",
        r"నమోదు\s*తేదీ\s*[:\-]?\s*(.+?)(?:\n|$)",
    ],
}


def clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = re.sub(r"\s+", " ", value).strip()
    value = value.strip(" .:;,'\"“”‘’—_|•[](){}")
    value = re.sub(r"\s*\|\s*", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value or None


def normalize_survey(value: str | None) -> str | None:
    value = clean(value)
    if not value:
        return None
    value = re.sub(r"\s+", "", value)
    return value


def normalize_area(value: str | None) -> str | None:
    value = clean(value)
    if not value:
        return None
    value = re.sub(r"\s+", " ", value)
    value = value.replace(",", ".")
    value = re.sub(r"\s*(acres?|acre)\b", " acres", value, flags=re.I)
    value = re.sub(r"\s+", " ", value)
    return value


def normalize_document_number(value: str | None) -> str | None:
    value = clean(value)
    if not value:
        return None
    compact = re.sub(r"\s+", "", value).upper()
    compact = re.sub(r"^DOC[^A-Z0-9]*", "DOC-", compact)
    compact = re.sub(r"^(DOC)-+", "DOC-", compact)
    compact = compact.replace("_", "-")
    # Keep the highly useful DOC-YYYY-NNNN family intact when OCR adds punctuation.
    m = re.search(r"(DOC-\d{4}-\d{2,8})", compact)
    return m.group(1) if m else compact


def postprocess(field: str, value: str | None) -> str | None:
    if field == "survey_number":
        return normalize_survey(value)
    if field == "area":
        return normalize_area(value)
    if field == "document_number":
        return normalize_document_number(value)
    return clean(value)


def extract_land_fields(text: str) -> dict[str, str | None]:
    out: dict[str, str | None] = {field: None for field in LABELS}
    for field, patterns in LABELS.items():
        for pattern in patterns:
            match = re.search(pattern, text, re.I | re.M)
            if match:
                out[field] = postprocess(field, match.group(1))
                break
    # A secondary document-number search is useful when the stamp overlaps the label.
    # Prefer any clean document-number token visible anywhere in the OCR text.
    doc_tokens = re.findall(r"\bDOC[-_/ ]?\d{4}[-_/ ]?[A-Z0-9]{3,8}\b", text, re.I)
    if doc_tokens:
        normalized = [normalize_document_number(t) for t in doc_tokens if normalize_document_number(t)]
        if normalized:
            normalized.sort(key=lambda x: (0 if re.fullmatch(r"DOC-\d{4}-\d{4}", x or "") else 1, len(x or "")))
            out["document_number"] = normalized[0]
    return out


def merge_candidates(candidate_sets: Iterable[dict[str, str | None]]) -> dict[str, str | None]:
    """Prefer the most frequent non-empty normalized candidate across OCR passes."""
    buckets: dict[str, list[str]] = {field: [] for field in LABELS}
    for result in candidate_sets:
        for field in LABELS:
            value = postprocess(field, result.get(field))
            if value:
                buckets[field].append(value)
    output: dict[str, str | None] = {}
    for field, values in buckets.items():
        if not values:
            output[field] = None
            continue
        counts: dict[str, int] = {}
        for value in values:
            counts[value] = counts.get(value, 0) + 1
        if field == "document_number":
            def key(v):
                canonical = bool(re.fullmatch(r"DOC-\d{4}-\d{4}", v or ""))
                return (canonical, counts[v], -len(v))
            output[field] = max(counts, key=key)
        else:
            output[field] = sorted(counts, key=lambda v: (counts[v], len(v)), reverse=True)[0]
    return output
