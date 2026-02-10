#!/usr/bin/env python3
"""
ورودی: فایل JSON خروجی Unstructured (elements با metadata.text_as_html برای Table).
خروجی: فقط اطلاعات AD 2.13 (DECLARED DISTANCES) با همان ساختار parser_ad2_13:
  section, source, runways (هر runway: RWY Designator + entries با TORA, TODA, ASDA, LDA, Remarks).
"""
from __future__ import annotations

import argparse
import html.parser
import json
import re
import sys
from pathlib import Path
from typing import Any, List, Dict

AD2_13_MARKERS = (
    "AD 2.13",
    "DECLARED DISTANCES",
    "RWY",
    "DESIGNATOR",
    "TORA",
    "TODA",
    "ASDA",
    "LDA",
    "Remarks",
)


def is_ad2_13_table(element: Dict[str, Any]) -> bool:
    if element.get("type") != "Table":
        return False
    text = (element.get("text") or "") + " "
    return any(m in text for m in AD2_13_MARKERS)


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
    t = s.strip() if isinstance(s, str) else s
    return t if t else None


def _clean_num(s: str) -> Any:
    v = _nil_to_null(s)
    if v is None:
        return None
    return str(v).strip()


def rows_to_ad2_13_runways(rows: List[List[str]]) -> List[Dict[str, Any]]:
    """
    از rows خام جدول AD 2.13، لیست runways با همان ساختار parser_ad2_13:
    [ { "RWY Designator": "11L", "entries": [ { TORA, TORA_unit, TODA, ... }, ... ] }, ... ]
    """
    runways_dict: Dict[str, List[Dict[str, Any]]] = {}
    current_rwy: str | None = None
    # ردیف‌های داده: یا با شماره باند در ستون اول، یا ادامه (ستون اول خالی)
    designator_re = re.compile(r"^\d{2}[LRCM]?$", re.I)
    header_keywords = ("RWY", "DESIGNATOR", "TORA", "TODA", "ASDA", "LDA", "REMARKS")

    for r in rows:
        if not r:
            continue
        # حداقل 5 ستون: RWY, TORA, TODA, ASDA, LDA و احتمالاً Remarks
        while len(r) < 6:
            r = r + [""]
        first = (r[0] or "").strip()
        if first and any(h in first.upper() for h in header_keywords):
            continue
        tora = _clean_num(r[1] if len(r) > 1 else "")
        toda = _clean_num(r[2] if len(r) > 2 else "")
        asda = _clean_num(r[3] if len(r) > 3 else "")
        lda = _clean_num(r[4] if len(r) > 4 else "")
        remarks = _nil_to_null(r[5] if len(r) > 5 else "")

        if designator_re.match(first):
            current_rwy = first.upper()
            if current_rwy not in runways_dict:
                runways_dict[current_rwy] = []
            entry = {
                "TORA": tora,
                "TORA_unit": "M",
                "TODA": toda,
                "TODA_unit": "M",
                "ASDA": asda,
                "ASDA_unit": "M",
                "LDA": lda,
                "LDA_unit": "M",
                "Remarks": remarks,
            }
            runways_dict[current_rwy].append(entry)
        elif current_rwy and (tora or toda or asda or lda):
            # ردیف ادامه (بدون شماره باند)
            entry = {
                "TORA": tora,
                "TORA_unit": "M",
                "TODA": toda,
                "TODA_unit": "M",
                "ASDA": asda,
                "ASDA_unit": "M",
                "LDA": lda,
                "LDA_unit": "M",
                "Remarks": remarks,
            }
            runways_dict[current_rwy].append(entry)

    # ترتیب باندها
    sorted_rwys = sorted(
        runways_dict.keys(),
        key=lambda x: (int(re.search(r"\d+", x).group()) if re.search(r"\d+", x) else 0, x),
    )
    result = []
    for rwy_nr in sorted_rwys:
        result.append({
            "RWY Designator": rwy_nr,
            "entries": runways_dict[rwy_nr],
        })
    return result


def extract_ad2_13_from_elements(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """استخراج runways از لیست elements (برای استفاده در API)."""
    runways_out: List[Dict[str, Any]] = []
    for el in elements:
        if not is_ad2_13_table(el):
            continue
        meta = el.get("metadata") or {}
        html_content = meta.get("text_as_html") or ""
        if not html_content:
            continue
        rows = html_table_to_json(html_content)
        runways = rows_to_ad2_13_runways(rows)
        runways_out.extend(runways)
        break
    return runways_out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="استخراج فقط AD 2.13 از خروجی Unstructured (همان ساختار خروجی parser_ad2_13)"
    )
    parser.add_argument(
        "elements_json",
        help="مسیر فایل JSON خروجی Unstructured",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="فایل خروجی JSON (پیش‌فرض: ad2_13_from_tables.json)",
    )
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

    runways_out: List[Dict[str, Any]] = []
    for el in elements:
        if not is_ad2_13_table(el):
            continue
        meta = el.get("metadata") or {}
        html_content = meta.get("text_as_html") or ""
        if not html_content:
            continue
        rows = html_table_to_json(html_content)
        runways = rows_to_ad2_13_runways(rows)
        runways_out.extend(runways)
        break

    if not runways_out:
        print("⚠️  هیچ جدول AD 2.13 در فایل ورودی یافت نشد.")
        out_data = {"section": "AD 2.13 DECLARED DISTANCES", "runways": [], "source": str(path)}
    else:
        out_data = {
            "section": "AD 2.13 DECLARED DISTANCES",
            "source": str(path),
            "runways": runways_out,
        }
        print(f"✅ {len(runways_out)} باند AD 2.13 استخراج شد.")

    out_path = args.output or "ad2_13_from_tables.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)
    print(f"💾 خروجی: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
