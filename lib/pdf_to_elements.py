#!/usr/bin/env python3
"""
تبدیل PDF به لیست elements با Unstructured (برای استفاده در API).
نصب: pip install "unstructured[pdf]"
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, List, Dict


def pdf_path_to_elements(
    pdf_path: str,
    strategy: str = "hi_res",
    infer_tables: bool = True,
) -> List[Dict[str, Any]]:
    """
    استخراج elements از PDF با Unstructured (محلی).
    خروجی: لیست دیکشنری با کلیدهای type, text, metadata (شامل text_as_html برای Table).
    """
    try:
        from unstructured.partition.pdf import partition_pdf
    except ImportError:
        raise RuntimeError(
            'unstructured نصب نیست. نصب: pip install "unstructured[pdf]"'
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
