from __future__ import annotations
import re
from database import list_feedback


def normalize_with_feedback(value: str | None, field_name: str) -> str | None:
    if value is None:return None
    current=value
    feedback=list_feedback()
    for row in feedback:
        if row["field_name"] != field_name:continue
        original=(row.get("original_value") or "").strip().lower()
        if original and current.strip().lower()==original:
            current=row["corrected_value"]
    return current


def learned_corrections():
    data={}
    for row in list_feedback():
        data.setdefault(row["field_name"],[]).append({"from":row.get("original_value"),"to":row.get("corrected_value"),"count":1})
    return data
