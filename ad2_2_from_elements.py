#!/usr/bin/env python3
"""
استخراج AD 2.2 (AERODROME GEOGRAPHICAL AND ADMINISTRATIVE DATA) از elements خروجی Unstructured.
خروجی همان ساختار parser_ad2_2: [ { field, value }, ... ].
"""
from __future__ import annotations

import html.parser
import re
from typing import Any, List, Dict


AD2_2_MARKERS = (
    "AD 2.2",
    "AERODROME GEOGRAPHICAL",
    "ARP coordinates",
    "Direction and distance from",
    "Elevation",
    "MAG VAR",
    "Types of traffic permitted",
)

TARGET_FIELDS = [
    "ARP coordinates and site at AD",
    "Direction and distance from (city)",
    "Elevation / Reference temperature",
    "MAG VAR / Annual change",
    "Types of traffic permitted (IFR/VFR)",
]

PATTERNS_FOR_FIELD = {
    "ARP coordinates and site at AD": ["arp coordinates", "coordinates and site"],
    "Direction and distance from (city)": ["direction and distance from", "direction and distance"],
    "Elevation / Reference temperature": ["elevation", "reference temperature"],
    "MAG VAR / Annual change": ["mag var", "annual change"],
    "Types of traffic permitted (IFR/VFR)": ["types of traffic", "traffic permitted"],
}


def _clean_value(s: str) -> str | None:
    if not s or not isinstance(s, str):
        return None
    s = re.sub(r"\s+", " ", s).strip()
    if s.upper() == "NIL":
        return None
    return s if s else None


def html_table_to_rows(html_str: str) -> List[List[str]]:
    rows: List[List[str]] = []
    current_row: List[str] = []
    current_cell: List[str] = []

    class Parser(html.parser.HTMLParser):
        def handle_starttag(self, tag: str, attrs: list) -> None:
            nonlocal current_row, current_cell
            if tag == "tr":
                current_row = []
                current_cell = []
            elif tag in ("td", "th"):
                current_cell = []

        def handle_endtag(self, tag: str) -> None:
            nonlocal current_row, current_cell, rows
            if tag in ("td", "th"):
                cell_text = " ".join(current_cell).strip()
                current_row.append(cell_text)
                current_cell = []
            elif tag == "tr":
                if current_row:
                    rows.append(current_row)
                current_row = []

        def handle_data(self, data: str) -> None:
            current_cell.append(data.strip())

    p = Parser()
    try:
        p.feed(html_str)
    except Exception:
        pass
    return rows


def _match_field(field_name: str) -> str | None:
    fl = field_name.lower()
    for target in TARGET_FIELDS:
        for pat in PATTERNS_FOR_FIELD.get(target, [target.lower()]):
            if pat in fl or any(w in fl for w in pat.split() if len(w) > 3):
                return target
    return None


def extract_ad2_2_from_elements(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    از لیست elements، جدول AD 2.2 را پیدا و فیلدها را استخراج کن.
    Returns: [ { "field": target_field, "value": "..." }, ... ]
    """
    result: List[Dict[str, Any]] = []
    found_fields = set()
    for el in elements:
        if el.get("type") != "Table":
            continue
        text = (el.get("text") or "") + " "
        if not any(m in text for m in AD2_2_MARKERS):
            continue
        meta = el.get("metadata") or {}
        html_content = meta.get("text_as_html") or ""
        if not html_content:
            continue
        rows = html_table_to_rows(html_content)
        for row in rows:
            if not row or len(row) < 2:
                continue
            row = [str(c).strip() if c else "" for c in row]
            field_name = ""
            field_value = ""
            if len(row) >= 3 and row[0].isdigit():
                field_name = row[1]
                field_value = row[2]
            else:
                field_name = row[0]
                field_value = row[1] if len(row) > 1 else ""
            if not field_name:
                continue
            target = _match_field(field_name)
            if target and target not in found_fields:
                val = _clean_value(field_value)
                if val is not None:
                    result.append({"field": target, "value": val})
                    found_fields.add(target)
        if len(found_fields) >= len(TARGET_FIELDS):
            break
    # ترتیب خروجی مطابق TARGET_FIELDS
    ordered = []
    for tf in TARGET_FIELDS:
        for item in result:
            if item["field"] == tf:
                ordered.append(item)
                break
    return ordered
