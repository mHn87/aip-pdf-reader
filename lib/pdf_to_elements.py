#!/usr/bin/env python3
"""
تبدیل PDF به لیست elements:
- اگر UNSTRUCTURED_API_KEY تنظیم باشد از Unstructured API استفاده می‌شود (مناسب Vercel).
- وگرنه از کتابخانهٔ محلی unstructured (نصب: pip install -r requirements-full.txt).
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path
from typing import Any, List, Dict

# Legacy Partition Endpoint (پیش‌فرض)
DEFAULT_UNSTRUCTURED_API_URL = "https://api.unstructuredapp.io/general/v0/general"
# Platform: https://platform.unstructuredapp.io/api/v1


def _pdf_to_elements_via_api(
    pdf_path: str,
    api_key: str,
    api_url: str,
    strategy: str = "hi_res",
) -> List[Dict[str, Any]]:
    """ارسال PDF به Unstructured API و دریافت elements."""
    path = Path(pdf_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"فایل یافت نشد: {pdf_path}")

    with open(path, "rb") as f:
        pdf_bytes = f.read()

    boundary = "--------PythonPDFBoundary"
    b = boundary.encode("utf-8")
    body = (
        b"--" + b + b"\r\nContent-Disposition: form-data; name=\"strategy\"\r\n\r\n" + strategy.encode("utf-8") + b"\r\n"
        + b"--" + b + b"\r\nContent-Disposition: form-data; name=\"files\"; filename=\"" + path.name.encode("utf-8") + b"\"\r\nContent-Type: application/pdf\r\n\r\n"
        + pdf_bytes + b"\r\n--" + b + b"--\r\n"
    )

    req = urllib.request.Request(
        api_url,
        data=body,
        method="POST",
        headers={
            "Accept": "application/json",
            "unstructured-api-key": api_key,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8") if e.fp else str(e)
        raise RuntimeError(f"Unstructured API error ({e.code}): {err_body}")
    except Exception as e:
        raise RuntimeError(f"Unstructured API request failed: {e}") from e

    # پاسخ API می‌تواند لیست elements باشد یا داخل کلیدی مثل "elements"
    raw_elements = data if isinstance(data, list) else data.get("elements", data)
    if not isinstance(raw_elements, list):
        raise RuntimeError("Unstructured API did not return a list of elements")

    out_list = []
    for i, el in enumerate(raw_elements):
        if isinstance(el, dict):
            d = el
        else:
            d = getattr(el, "__dict__", {}) or {}
        meta = d.get("metadata") or {}
        if not isinstance(meta, dict):
            meta = dict(meta) if hasattr(meta, "items") else {}
        out_list.append({
            "element_id": d.get("element_id") or d.get("id") or f"elem-{i}",
            "type": d.get("type"),
            "text": d.get("text", ""),
            "metadata": meta,
        })
    return out_list


def pdf_path_to_elements(
    pdf_path: str,
    strategy: str = "hi_res",
    infer_tables: bool = True,
) -> List[Dict[str, Any]]:
    """
    استخراج elements از PDF.
    اگر UNSTRUCTURED_API_KEY تنظیم باشد از API استفاده می‌شود؛ وگرنه از کتابخانهٔ محلی.
    خروجی: لیست دیکشنری با کلیدهای type, text, metadata (شامل text_as_html برای Table).
    """
    api_key = (os.environ.get("UNSTRUCTURED_API_KEY") or "").strip()
    if api_key:
        api_url = (os.environ.get("UNSTRUCTURED_API_URL") or DEFAULT_UNSTRUCTURED_API_URL).strip()
        return _pdf_to_elements_via_api(pdf_path, api_key=api_key, api_url=api_url, strategy=strategy)

    try:
        from unstructured.partition.pdf import partition_pdf
    except ImportError:
        raise RuntimeError(
            "PDF parsing is not available: set UNSTRUCTURED_API_KEY in Vercel, "
            "or install locally: pip install -r requirements-full.txt"
        )

    path = Path(pdf_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"فایل یافت نشد: {pdf_path}")
    elements = partition_pdf(
        filename=str(path),
        strategy=strategy,
        infer_table_structure=infer_tables,
    )
    out_list = []
    for i, el in enumerate(elements):
        d = {}
        if hasattr(el, "to_dict"):
            try:
                d = el.to_dict()
            except Exception:
                pass
        if not d:
            d = {
                "type": getattr(el, "type", None) or type(el).__name__,
                "text": getattr(el, "text", ""),
                "metadata": getattr(el, "metadata", {}) or {},
            }
        meta = d.get("metadata") or {}
        if isinstance(meta, dict):
            meta = dict(meta)
        else:
            meta = {}
        out_list.append({
            "element_id": d.get("element_id") or d.get("id") or f"elem-{i}",
            "type": d.get("type"),
            "text": d.get("text", ""),
            "metadata": meta,
        })
    return out_list
