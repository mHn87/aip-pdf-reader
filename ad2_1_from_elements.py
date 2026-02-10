#!/usr/bin/env python3
"""
استخراج AD 2.1 (AERODROME LOCATION INDICATOR AND NAME) از elements خروجی Unstructured.
خروجی همان ساختار parser_ad2_1: { name, country, aip }.
"""
from __future__ import annotations

import re
from typing import Any, List, Dict


AD2_1_MARKERS = ("AD 2.1", "AERODROME LOCATION INDICATOR", "LOCATION INDICATOR AND NAME")


def extract_ad2_1_from_elements(elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    از لیست elements، فیلدهای AD 2.1 را استخراج کن.
    Returns: { "name": ICAO, "country": City, "aip": Airport Name } یا مقادیر None.
    """
    result = {"name": None, "country": None, "aip": None}
    combined = []
    found_section = False
    for el in elements:
        text = (el.get("text") or "").strip()
        if not text:
            continue
        if any(m in text for m in AD2_1_MARKERS):
            found_section = True
        if found_section:
            combined.append(text)
            # الگو: OIAA - Abadan / Abadan International یا OIII - TEHRAN / Mehrabad International
            pattern_main = r"([A-Z]{4})\s*-\s*([A-Za-z]+)\s*/\s*([A-Za-z\s]+?)(?:\s+International)?(?:\n|$)"
            match = re.search(pattern_main, text)
            if match:
                result["name"] = match.group(1).strip().upper()
                result["country"] = match.group(2).strip().title()
                aip = match.group(3).strip()
                if aip and "international" not in aip.lower():
                    aip = aip + " International"
                result["aip"] = aip
                return result
        if found_section and ("AD 2.2" in text or "AD2.2" in text):
            break
    full_text = " ".join(combined)
    if not result["name"]:
        header = re.search(r"AIP\s+AD\s+\d+-\d+\s+([A-Z]{4})", full_text)
        if header:
            icao = header.group(1)
            name_match = re.search(
                rf"{icao}\s*-\s*([A-Z][A-Za-z]+)\s*/\s*([A-Za-z\s]+?)(?:International|INTL|\n)",
                full_text,
            )
            if name_match:
                result["name"] = icao
                result["country"] = name_match.group(1).strip().title()
                result["aip"] = (name_match.group(2).strip() + " International").strip()
    return result
