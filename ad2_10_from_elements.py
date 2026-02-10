#!/usr/bin/env python3
"""
ورودی: فایل JSON خروجی Unstructured (elements با metadata.text_as_html برای Table).
خروجی: فقط اطلاعات AD 2.10 (AERODROME OBSTACLES) با همان ساختار parser_ad2_10:
  section, source, obstacles (dict: کلید = RWY/Area مثلاً "11R / APCH"، مقدار = لیست موانع با Coordinates و Obstacle type...).
"""
from __future__ import annotations

import argparse
import html.parser
import json
import re
import sys
from pathlib import Path
from typing import Any, List, Dict

AD2_10_MARKERS = (
    "AD 2.10",
    "AERODROME OBSTACLES",
    "In approach",
    "TKOF",
    "RWY",
    "Area affected",
    "Obstacle",
    "Coordinates",
)


def is_ad2_10_table(element: Dict[str, Any]) -> bool:
    if element.get("type") != "Table":
        return False
    text = (element.get("text") or "") + " "
    return any(m in text for m in AD2_10_MARKERS)


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


def parse_rwy_cell(cell_text: str) -> List[str]:
    """
    استخراج کلیدهای RWY از سلول؛ مثلاً "11R / APCH" یا "11L/R / APCH\\n29L / TKOF".
    """
    if not cell_text or not isinstance(cell_text, str):
        return []
    keys = set()
    lines = cell_text.strip().split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        match = re.match(r"^(\d{2})([LRC]?(?:/[LRC])?)\s*/\s*(APCH|TKOF)", line, re.IGNORECASE)
        if not match:
            continue
        rwy_num = match.group(1)
        rwy_suffix = (match.group(2) or "").upper()
        rwy_type = match.group(3).upper()
        if not rwy_suffix:
            keys.add(f"{rwy_num}L / {rwy_type}")
            keys.add(f"{rwy_num}R / {rwy_type}")
        elif "/" in rwy_suffix:
            for p in rwy_suffix.replace("/", ""):
                keys.add(f"{rwy_num}{p} / {rwy_type}")
        else:
            keys.add(f"{rwy_num}{rwy_suffix} / {rwy_type}")
    return list(keys)


def rows_to_ad2_10_obstacles(rows: List[List[str]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    از rows خام جدول AD 2.10، دیکشنری obstacles با همان ساختار parser_ad2_10:
    { "11R / APCH": [ { "Coordinates": "...", "Obstacle type Elevation/HGT Markings/LGT": "..." }, ... ], ... }
    """
    result: Dict[str, List[Dict[str, Any]]] = {}
    last_rwy_keys: List[str] = []
    skip_headers = ("In approach / TKOF areas", "RWY/Area affected", "1", "a")

    for r in rows:
        if not r or len(r) < 3:
            continue
        rwy_cell = (r[0] or "").strip()
        obstacle_cell = (r[1] or "").strip() if len(r) > 1 else ""
        coords_cell = (r[2] or "").strip() if len(r) > 2 else ""

        if rwy_cell and rwy_cell in skip_headers:
            continue
        if not obstacle_cell and not coords_cell:
            continue

        if rwy_cell:
            keys = parse_rwy_cell(rwy_cell)
            if keys:
                last_rwy_keys = keys
            else:
                continue
        else:
            keys = last_rwy_keys
        if not keys:
            continue

        coords = coords_cell if coords_cell else None
        info = obstacle_cell if obstacle_cell else None
        obstacle_data = {
            "Coordinates": coords,
            "Obstacle type Elevation/HGT Markings/LGT": info,
        }
        for key in keys:
            if key not in result:
                result[key] = []
            result[key].append(obstacle_data)

    return result


def extract_ad2_10_from_elements(elements: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """استخراج obstacles از لیست elements (برای استفاده در API)."""
    obstacles_out: Dict[str, List[Dict[str, Any]]] = {}
    for el in elements:
        if not is_ad2_10_table(el):
            continue
        meta = el.get("metadata") or {}
        html_content = meta.get("text_as_html") or ""
        if not html_content:
            continue
        rows = html_table_to_json(html_content)
        obs = rows_to_ad2_10_obstacles(rows)
        for k, v in obs.items():
            obstacles_out.setdefault(k, []).extend(v)
        break
    return obstacles_out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="استخراج فقط AD 2.10 از خروجی Unstructured (همان ساختار خروجی parser_ad2_10)"
    )
    parser.add_argument(
        "elements_json",
        help="مسیر فایل JSON خروجی Unstructured",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="فایل خروجی JSON (پیش‌فرض: ad2_10_from_tables.json)",
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

    obstacles_out: Dict[str, List[Dict[str, Any]]] = {}
    for el in elements:
        if not is_ad2_10_table(el):
            continue
        meta = el.get("metadata") or {}
        html_content = meta.get("text_as_html") or ""
        if not html_content:
            continue
        rows = html_table_to_json(html_content)
        obs = rows_to_ad2_10_obstacles(rows)
        for k, v in obs.items():
            obstacles_out.setdefault(k, []).extend(v)
        break

    if not obstacles_out:
        print("⚠️  هیچ جدول AD 2.10 در فایل ورودی یافت نشد.")
        out_data = {"section": "AD 2.10 AERODROME OBSTACLES", "obstacles": {}, "source": str(path)}
    else:
        out_data = {
            "section": "AD 2.10 AERODROME OBSTACLES",
            "source": str(path),
            "obstacles": obstacles_out,
        }
        total = sum(len(v) for v in obstacles_out.values())
        print(f"✅ {len(obstacles_out)} کلید RWY، {total} مانع استخراج شد.")

    out_path = args.output or "ad2_10_from_tables.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)
    print(f"💾 خروجی: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
