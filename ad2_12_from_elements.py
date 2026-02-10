#!/usr/bin/env python3
"""
ورودی: فایل JSON خروجی Unstructured (elements با metadata.text_as_html برای Table).
خروجی: فقط اطلاعات AD 2.12 (RUNWAY PHYSICAL CHARACTERISTICS) به‌صورت JSON.
"""
from __future__ import annotations

import argparse
import html.parser
import json
import re
import sys
from pathlib import Path
from typing import Any, List, Dict


AD2_12_MARKERS = (
    "AD 2.12",
    "RUNWAY PHYSICAL CHARACTERISTICS",
    "Designations",
    "RWY NR",
    "TRUE BRG",
    "Dimensions of RW",
)


def is_ad2_12_table(element: Dict[str, Any]) -> bool:
    if element.get("type") != "Table":
        return False
    text = (element.get("text") or "") + " "
    return any(m in text for m in AD2_12_MARKERS)


def html_table_to_json(html_str: str) -> List[List[str]]:
    rows: List[List[str]] = []
    current_row: List[str] = []
    current_cell: List[str] = []

    class TableParser(html.parser.HTMLParser):
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

    parser = TableParser()
    try:
        parser.feed(html_str)
    except Exception:
        pass
    return rows


def _nil_to_null(s: str) -> Any:
    if s is None or (isinstance(s, str) and s.strip().upper() in ("", "NIL")):
        return None
    return s.strip() if isinstance(s, str) else s


def rows_to_ad2_12_runways(rows: List[List[str]]) -> List[Dict[str, Any]]:
    designators = ("14L", "32R", "14R", "32L")
    runway_rows = [r for r in rows if r and (r[0] or "").strip() in designators]
    slope_swy_rows = [
        r for r in rows
        if r and (r[0] or "").strip() and (
            (r[0] or "").strip() in ("0.0%", "0.003%")
            or ("%" in (r[0] or "") and (r[0] or "").replace(".", "").replace("%", "").strip().isdigit())
        )
    ]
    if not runway_rows:
        return []

    runways: List[Dict[str, Any]] = []
    for idx, r in enumerate(runway_rows[:4]):
        while len(r) < 6:
            r = r + [""]
        designator = (r[0] or "").strip()
        true_brg = (r[1] or "").replace("°", "").strip()
        true_brg = re.sub(r"(\d)(GEO)", r"\1 \2", true_brg, flags=re.I)
        dims = (r[2] or "").strip()
        if dims and " M" not in dims.upper():
            dims = dims + " M"
        strength = (r[3] or "").strip()
        thr_coords = (r[4] or "").strip()
        thr_coords = re.sub(r"GUND\s*[-]?\s*(\d+)\s*FT", r"GUND \1FT", thr_coords, flags=re.I)
        thr_elev = (r[5] or "").strip()

        slope_val = swy_val = cwy_val = strip_val = ofz_val = None
        if idx < len(slope_swy_rows):
            sr = slope_swy_rows[idx]
            if len(sr) >= 1:
                slope_val = _nil_to_null(sr[0])
            if len(sr) >= 2:
                swy_val = _nil_to_null(sr[1])
            if len(sr) >= 3:
                cwy_val = _nil_to_null(sr[2])
            if len(sr) >= 4:
                strip_val = _nil_to_null(sr[3])
            if len(sr) >= 5:
                ofz_val = _nil_to_null(sr[4])

        runways.append({
            "Designations": designator,
            "TRUE BRG": true_brg or None,
            "Dimensions of RWY": dims or None,
            "Strength": strength or None,
            "THR coordinates": thr_coords or None,
            "THR elevation": thr_elev or None,
            "Slope": slope_val,
            "SWY dimensions": swy_val,
            "CWY dimensions": cwy_val,
            "Strip dimensions": strip_val,
            "RESA": None,
            "OFZ": ofz_val,
        })
    return runways


def extract_ad2_12_from_elements(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """استخراج runways از لیست elements (برای استفاده در API)."""
    runways_out: List[Dict[str, Any]] = []
    for el in elements:
        if not is_ad2_12_table(el):
            continue
        meta = el.get("metadata") or {}
        html_content = meta.get("text_as_html") or ""
        if not html_content:
            continue
        rows = html_table_to_json(html_content)
        runways = rows_to_ad2_12_runways(rows)
        runways_out.extend(runways)
        break
    return runways_out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="استخراج فقط AD 2.12 از خروجی Unstructured"
    )
    parser.add_argument("elements_json", help="مسیر فایل JSON خروجی Unstructured")
    parser.add_argument("-o", "--output", default=None, help="فایل خروجی JSON")
    args = parser.parse_args()

    path = Path(args.elements_json)
    if not path.exists():
        print(f"❌ فایل یافت نشد: {path}")
        return 1

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    elements = data.get("elements", data) if isinstance(data, dict) else data
    if not isinstance(elements, list):
        print("❌ ساختار فایل نامعتبر؛ انتظار elements (لیست) می‌رود.")
        return 1

    runways_out = extract_ad2_12_from_elements(elements)
    if not runways_out:
        out_data = {"section": "AD 2.12 RUNWAY PHYSICAL CHARACTERISTICS", "runways": [], "source": str(path)}
    else:
        out_data = {
            "section": "AD 2.12 RUNWAY PHYSICAL CHARACTERISTICS",
            "source": str(path),
            "runways": runways_out,
        }
        print(f"✅ {len(runways_out)} باند AD 2.12 استخراج شد.")

    out_path = args.output or "ad2_12_from_tables.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)
    print(f"💾 خروجی: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
