from __future__ import annotations
from pathlib import Path
from statistics import mean
import re
import pymupdf
import pytesseract
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from pytesseract import Output
from extractor import extract_land_fields, merge_candidates, postprocess

SUPPORTED_LANGUAGES = {
    "en": {"label": "English", "tesseract": "eng"},
    "te": {"label": "Telugu", "tesseract": "tel"},
    "hi": {"label": "Hindi", "tesseract": "hin"},
    "kn": {"label": "Kannada", "tesseract": "kan"},
    "ta": {"label": "Tamil", "tesseract": "tam"},
    "bn": {"label": "Bengali", "tesseract": "ben"},
    "mr": {"label": "Marathi", "tesseract": "mar"},
    "gu": {"label": "Gujarati", "tesseract": "guj"},
}


def available_tesseract_languages():
    try:
        installed = set(pytesseract.get_languages(config=""))
    except Exception:
        return []
    return [code for code, meta in SUPPORTED_LANGUAGES.items() if meta["tesseract"] in installed]


def resolve_languages(requested: str):
    requested = (requested or "auto").lower().strip()
    try:
        installed = set(pytesseract.get_languages(config=""))
    except Exception:
        installed = set()
    if requested == "auto":
        usable = [SUPPORTED_LANGUAGES[c]["tesseract"] for c in ("en", "te", "hi") if SUPPORTED_LANGUAGES[c]["tesseract"] in installed]
        usable = usable or (["eng"] if "eng" in installed else list(installed)[:1] or ["eng"])
        return "+".join(usable), "auto", bool(usable), "Automatic language selection across available OCR packs"
    meta = SUPPORTED_LANGUAGES.get(requested)
    if not meta:
        raise ValueError(f"Unsupported OCR language: {requested}")
    tess = meta["tesseract"]
    if tess in installed:
        return tess, requested, True, f"{meta['label']} OCR"
    fallback = "eng" if "eng" in installed else (next(iter(installed)) if installed else "eng")
    return fallback, requested, False, f"{meta['label']} OCR pack is unavailable; used English/available fallback OCR"


def preprocess(image: Image.Image, mode: str):
    image = image.convert("L")
    image = ImageOps.autocontrast(image)
    image = image.filter(ImageFilter.MedianFilter(size=3))
    image = image.filter(ImageFilter.SHARPEN)
    if image.width < 2400:
        scale = 2400 / image.width
        image = image.resize((int(image.width * scale), int(image.height * scale)))
    if mode == "handwritten":
        image = ImageEnhance.Contrast(image).enhance(1.45)
        image = ImageEnhance.Sharpness(image).enhance(1.35)
        return image
    if mode == "land_record":
        image = ImageEnhance.Contrast(image).enhance(1.25)
        image = ImageEnhance.Sharpness(image).enhance(1.25)
        return image
    image = ImageEnhance.Contrast(image).enhance(1.15)
    return image


def _remove_colored_stamp(image: Image.Image) -> Image.Image:
    """Suppress blue/purple ink stamps so they do not corrupt nearby printed text."""
    rgb = np.array(image.convert("RGB"))
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    # Strong blue/purple ink is usually much more saturated than the beige paper.
    mask = cv2.inRange(hsv, np.array([95, 55, 35], dtype=np.uint8), np.array([175, 255, 255], dtype=np.uint8))
    mask = cv2.medianBlur(mask, 3)
    if int(mask.sum()) == 0:
        return image.convert("L")
    restored = cv2.inpaint(bgr, mask, 3, cv2.INPAINT_TELEA)
    gray = cv2.cvtColor(restored, cv2.COLOR_BGR2GRAY)
    return Image.fromarray(gray)


def _variants(image: Image.Image, mode: str):
    base_input = _remove_colored_stamp(image)
    base = preprocess(base_input, mode)
    variants = [base]
    threshold = 178 if mode != "handwritten" else 160
    variants.append(base.point(lambda p: 255 if p > threshold else 0))
    soft = ImageEnhance.Contrast(base).enhance(1.08)
    variants.append(soft)
    if mode == "land_record":
        variants.append(base.point(lambda p: 255 if p > 195 else 0))
    return variants


def ocr_image(image: Image.Image, lang: str, mode: str):
    texts = []
    word_rows = []
    confidences = []
    for prepared in _variants(image, mode):
        for psm in (11, 6):
            config = f"--oem 3 --psm {psm}"
            data = pytesseract.image_to_data(prepared, lang=lang, config=config, output_type=Output.DICT)
            lines = {}
            words = []
            confs = []
            for i, raw in enumerate(data["text"]):
                text = (raw or "").strip()
                try:
                    conf = float(data["conf"][i])
                except Exception:
                    conf = -1
                if not text:
                    continue
                key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
                lines.setdefault(key, []).append(text)
                words.append((text, conf))
                if conf >= 0:
                    confs.append(conf)
            raw_text = "\n".join(" ".join(v) for v in lines.values()).strip()
            if raw_text:
                texts.append(raw_text)
                word_rows.append(words)
                confidences.append(mean(confs) if confs else 0.0)
    return texts, word_rows, confidences


def _field_confidence(fields, raw_candidates, word_candidates, overall):
    confidence = {field: 0.0 for field in fields}
    for field, value in fields.items():
        if not value:
            continue
        scores = []
        needle = postprocess(field, value) or ""
        for raw, words in zip(raw_candidates, word_candidates):
            normalized = postprocess(field, extract_land_fields(raw).get(field))
            if normalized and normalized == needle:
                scores.append(mean([c for _, c in words if c >= 0]) if words else overall)
        base = max(scores) if scores else overall
        # Multiple independent OCR passes agreeing on the same field are strong evidence.
        agreement = sum(1 for raw in raw_candidates if postprocess(field, extract_land_fields(raw).get(field)) == needle)
        bonus = min(15.0, max(0, agreement - 1) * 5.0)
        confidence[field] = round(min(99.0, base + bonus), 1)
    return confidence


def _pdf_pages(path: Path):
    doc = pymupdf.open(str(path))
    try:
        for page in doc:
            pix = page.get_pixmap(matrix=pymupdf.Matrix(3, 3), alpha=False)
            yield Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    finally:
        doc.close()


def extract_land_record(file_path: str, language_code="auto", mode="land_record"):
    if mode not in {"printed", "land_record", "handwritten"}:
        raise ValueError("Unsupported recognition mode")
    tess, selected, available, status = resolve_languages(language_code)
    path = Path(file_path)
    images = list(_pdf_pages(path)) if path.suffix.lower() == ".pdf" else [Image.open(path)]
    raw_candidates = []
    word_candidates = []
    pass_scores = []
    for image in images:
        texts, words, confidences = ocr_image(image, tess, mode)
        raw_candidates.extend(texts)
        word_candidates.extend(words)
        pass_scores.extend(confidences)
    merged_raw = "\n\n".join(dict.fromkeys(t for t in raw_candidates if t))
    candidates = [extract_land_fields(text) for text in raw_candidates]
    fields = merge_candidates(candidates)
    # A final whole-text extraction can recover fields that appear only after deduplicating lines.
    merged_fields = extract_land_fields(merged_raw)
    fields = merge_candidates([fields, merged_fields])
    overall = round(mean(pass_scores), 1) if pass_scores else 0.0
    confidence = _field_confidence(fields, raw_candidates + [merged_raw], word_candidates + [[]], overall)
    if mode == "land_record":
        note = "Field-aware multi-pass land-record OCR with layout-tolerant extraction"
    elif mode == "handwritten":
        note = "Handwriting-oriented preprocessing; uncertain fields require human verification"
    else:
        note = "Multi-pass printed-document OCR"
    return {
        "raw_text": merged_raw,
        "fields": fields,
        "confidence": confidence,
        "language_requested": language_code,
        "language_used": selected,
        "language_available": available,
        "language_status": status,
        "ocr_mode": mode,
        "recognition_note": note,
        "overall_confidence": overall,
    }
