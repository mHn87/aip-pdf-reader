#!/usr/bin/env python3
"""
تبدیل PDF به لیست elements با Unstructured (API یا محلی).
اگر UNSTRUCTURED_API_KEY تنظیم باشد از API استفاده می‌شود (مناسب Vercel).
در غیر این صورت از کتابخانهٔ محلی (pip install -r requirements-full.txt).
"""
from __future__ import annotations

import os
import json
import uuid
from pathlib import Path
from typing import Any, List, Dict

DEFAULT_API_URL = "https://api.unstructuredapp.io/general/v0/general"


def _pdf_to_elements_via_api(pdf_path: str, api_key: str, api_url: str) -> List[Dict[str, Any]]:
    """ارسال PDF به Unstructured API و دریافت elements."""
    import urllib.request

    path = Path(pdf_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"فایل یافت نشد: {pdf_path}")

    boundary = uuid.uuid4().hex
    with open(path, "rb") as f:
        file_bytes = f.read()
    filename = path.name

    body_start = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="files"; filename="{filename}"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode("utf-8")
    body_end = (
        f"\r\n--{boundary}\r\n"
        f'Content-Disposition: form-data; name="strategy"\r\n\r\nauto\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="output_format"\r\n\r\napplication/json\r\n'
        f"--{boundary}--\r\n"
    ).encode("utf-8")
    body = body_start + file_bytes + body_end

    req = urllib.request.Request(
        api_url,
        data=body,
        method="POST",
        headers={
            "unstructured-api-key": api_key,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        raw = resp.read().decode("utf-8")
    data = json.loads(raw)
    elements_raw = data if isinstance(data, list) else data.get("elements", data)
    if not elements_raw:
        return []

    out_list = []
    for i, el in enumerate(elements_raw):
        if isinstance(el, dict):
            meta = dict(el.get("metadata") or {})
            out_list.append({
                "element_id": el.get("element_id") or el.get("id") or f"elem-{i}",
                "type": el.get("type"),
                "text": el.get("text", ""),
                "metadata": meta,
            })
        else:
            out_list.append({
                "element_id": f"elem-{i}",
                "type": getattr(el, "type", None),
                "text": getattr(el, "text", ""),
                "metadata": dict(getattr(el, "metadata", {}) or {}),
            })
    return out_list


def _pdf_to_elements_local(pdf_path: str, strategy: str, infer_tables: bool) -> List[Dict[str, Any]]:
    """استخراج با کتابخانهٔ محلی unstructured."""
    from unstructured.partition.pdf import partition_pdf

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
    api_key = os.environ.get("UNSTRUCTURED_API_KEY", "").strip()
    if api_key:
        api_url = os.environ.get("UNSTRUCTURED_API_URL", "").strip() or DEFAULT_API_URL
        return _pdf_to_elements_via_api(pdf_path, api_key, api_url)

    try:
        return _pdf_to_elements_local(pdf_path, strategy, infer_tables)
    except ImportError:
        raise RuntimeError(
            "PDF parsing is not available on this deployment. "
            "Set UNSTRUCTURED_API_KEY in environment, or install locally: pip install -r requirements-full.txt"
        )
