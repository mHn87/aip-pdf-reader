#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
پارسر دقیق برای AD 2.2 - AERODROME GEOGRAPHICAL AND ADMINISTRATIVE DATA
"""

import json
import re
import sys
from pathlib import Path
import pdfplumber


def deep_clean_text(text: str) -> str:
    """
    تمیز کردن عمیق متن - حذف همه کاراکترهای غیرعادی
    فقط حروف، اعداد، فاصله و چند کاراکتر ضروری نگه داشته می‌شود
    """
    if not text:
        return ""
    
    text = str(text)
    
    # 1. حذف همه Unicode Private Use Area characters
    text = re.sub(r'[\ue000-\uf8ff]', '', text)
    
    # 2. حذف همه Unicode symbols و arrows
    text = re.sub(r'[\u2190-\u21ff]', '', text)  # Arrows
    text = re.sub(r'[\u2500-\u257f]', '', text)  # Box Drawing
    text = re.sub(r'[\u2580-\u259f]', '', text)  # Block Elements
    text = re.sub(r'[\u25a0-\u25ff]', '', text)  # Geometric Shapes
    text = re.sub(r'[\u2600-\u26ff]', '', text)  # Miscellaneous Symbols
    text = re.sub(r'[\u2700-\u27bf]', '', text)  # Dingbats
    
    # 3. حذف degree symbols
    text = re.sub(r'[\u00b0\u00ba]', '', text)
    
    # 4. حذف control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    # 5. فقط حروف، اعداد، فاصله، newline و چند کاراکتر ضروری نگه دار
    text = re.sub(r'[^\w\s\n/.()%:,+-]', '', text, flags=re.IGNORECASE)
    
    return text


def clean_value(text: str):
    """تمیز کردن مقدار برای خروجی JSON"""
    if not text:
        return None
    
    text = deep_clean_text(text).strip()
    
    # تبدیل NIL به None
    if text.upper() == "NIL":
        return None
    
    # تمیز کردن فاصله‌های اضافی
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text if text else None


def extract_ad2_2(pdf_path: str) -> list:
    """
    استخراج دقیق داده‌های AD 2.2 از PDF
    
    Returns:
        list: آرایه‌ای از مقادیر 5 فیلد مورد نظر
    """
    result = []
    
    # فیلدهای مورد نظر با الگوهای تطبیق
    target_fields_map = {
        "ARP coordinates and site at AD": [
            "ARP coordinates and site at AD",
            "ARP coordinates",
            "coordinates and site"
        ],
        "Direction and distance from (city)": [
            "Direction and distance from (city)",
            "Direction and distance from",
            "Direction and distance"
        ],
        "Elevation / Reference temperature": [
            "Elevation / Reference temperature",
            "Elevation/Reference temperature",
            "Elevation / Reference"
        ],
        "MAG VAR / Annual change": [
            "MAG VAR / Annual change",
            "MAG VAR/Annual change",
            "MAG VAR / Annual"
        ],
        "Types of traffic permitted (IFR/VFR)": [
            "Types of traffic permitted (IFR/VFR)",
            "Types of traffic permitted",
            "traffic permitted"
        ]
    }
    
    target_fields = list(target_fields_map.keys())
    
    print(f"🔍 در حال جستجوی AD 2.2 در PDF: {pdf_path}")
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # استخراج متن صفحه
            text = page.extract_text()
            
            # بررسی اینکه آیا این صفحه شامل AD 2.2 است
            if not text:
                continue
            
            if not ("AD 2.2" in text or "AD2.2" in text or "AERODROME GEOGRAPHICAL" in text):
                continue
            
            print(f"✅ صفحه {page_num + 1} پیدا شد: AD 2.2")
            
            # استخراج جداول از صفحه با تنظیمات بهتر
            try:
                # ابتدا با تنظیمات خطوط سعی می‌کنیم
                tables = page.extract_tables(table_settings={
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                })
            except:
                try:
                    # اگر نشد، با تنظیمات پیش‌فرض
                    tables = page.extract_tables()
                except:
                    tables = []
            
            for table_idx, table in enumerate(tables):
                if not table or len(table) == 0:
                    continue
                
                # بررسی اینکه آیا این جدول مربوط به AD 2.2 است
                table_text = ""
                for row in table:
                    if row:
                        table_text += " ".join([str(cell) if cell else "" for cell in row])
                
                # اگر جدول شامل فیلدهای مورد نظر باشد
                has_target_fields = any(
                    any(pattern.lower() in table_text.lower() for pattern in patterns)
                    for patterns in target_fields_map.values()
                )
                
                if not has_target_fields:
                    continue
                
                print(f"📊 جدول {table_idx + 1} پیدا شد")
                
                # پردازش جدول - ساختار: [شماره, عنوان فیلد, مقدار]
                found_fields = set()
                
                for row in table:
                    if not row:
                        continue
                    
                    # حذف None و تبدیل به string
                    row = [str(cell).strip() if cell else "" for cell in row]
                    
                    # حداقل باید 2 ستون داشته باشد
                    if len(row) < 2:
                        continue
                    
                    # پیدا کردن ستون‌های مختلف
                    # ممکن است ساختار متفاوت باشد: [شماره, عنوان, مقدار] یا [عنوان, مقدار]
                    field_name = ""
                    field_value = ""
                    
                    # اگر ستون اول عدد است، پس ساختار [شماره, عنوان, مقدار] است
                    if row[0].isdigit() and len(row) >= 3:
                        field_name = row[1]
                        field_value = row[2] if len(row) > 2 else ""
                    # در غیر این صورت [عنوان, مقدار]
                    elif len(row) >= 2:
                        field_name = row[0]
                        field_value = row[1] if len(row) > 1 else ""
                    
                    if not field_name:
                        continue
                    
                    # تمیز کردن نام فیلد
                    field_name = re.sub(r'\s+', ' ', field_name).strip()
                    field_value = re.sub(r'\s+', ' ', field_value).strip()
                    
                    # بررسی تطابق با فیلدهای مورد نظر
                    for target_field, patterns in target_fields_map.items():
                        if target_field in found_fields:
                            continue
                        
                        # بررسی تطابق
                        field_name_lower = field_name.lower()
                        for pattern in patterns:
                            pattern_lower = pattern.lower()
                            if (pattern_lower in field_name_lower or 
                                field_name_lower in pattern_lower or
                                any(word in field_name_lower for word in pattern_lower.split() if len(word) > 3)):
                                
                                # تمیز کردن مقدار
                                field_value_clean = clean_value(field_value.replace('\n', ' '))
                                
                                result.append({
                                    "field": target_field,
                                    "value": field_value_clean
                                })
                                
                                found_fields.add(target_field)
                                print(f"  ✓ {target_field}: {field_value_clean[:60]}...")
                                break
                
                # اگر همه فیلدها پیدا شدند، متوقف شو
                if len(found_fields) >= len(target_fields):
                    break
            
            # اگر داده پیدا شد، از جستجو خارج شو
            if len(result) >= len(target_fields):
                break
    
    # اگر با روش جدول پیدا نشد، از متن استخراج کن
    if not result or len(result) < len(target_fields):
        print("⚠️  داده‌ها از جدول کامل استخراج نشد، در حال جستجو در متن...")
        text_result = extract_from_text(pdf_path, target_fields)
        # ترکیب نتایج
        existing_fields = {item["field"] for item in result}
        for item in text_result:
            if item["field"] not in existing_fields:
                result.append(item)
    
    # مرتب‌سازی بر اساس ترتیب فیلدهای مورد نظر
    result_sorted = []
    for target_field in target_fields:
        for item in result:
            if item["field"] == target_field:
                result_sorted.append(item)
                break
    
    return result_sorted


def extract_from_text(pdf_path: str, target_fields: list) -> list:
    """استخراج از متن PDF در صورت عدم موفقیت در استخراج جدول"""
    result = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            
            if not text or ("AD 2.2" not in text and "AD2.2" not in text):
                continue
            
            print(f"📄 استخراج از متن صفحه {page_num + 1}")
            
            # الگوهای جستجو برای هر فیلد
            patterns = {
                "ARP coordinates and site at AD": [
                    r"ARP coordinates and site at AD[:\s]+([^\n]+(?:\n[^\d]+[^\n]+)?)",
                    r"1\s+ARP coordinates[^\n]+([^\n]+(?:\n[^\n]+)?)"
                ],
                "Direction and distance from (city)": [
                    r"Direction and distance from \(city\)[:\s]+([^\n]+)",
                    r"2\s+Direction[^\n]+([^\n]+)"
                ],
                "Elevation / Reference temperature": [
                    r"Elevation\s*/\s*Reference temperature[:\s]+([^\n]+)",
                    r"3\s+Elevation[^\n]+([^\n]+)"
                ],
                "MAG VAR / Annual change": [
                    r"MAG VAR\s*/\s*Annual change[:\s]+([^\n]+)",
                    r"4\s+MAG VAR[^\n]+([^\n]+)"
                ],
                "Types of traffic permitted (IFR/VFR)": [
                    r"Types of traffic permitted\s*\(IFR/VFR\)[:\s]+([^\n]+)",
                    r"6\s+Types of traffic[^\n]+([^\n]+)"
                ]
            }
            
            for target_field in target_fields:
                if any(item["field"] == target_field for item in result):
                    continue
                
                if target_field in patterns:
                    for pattern in patterns[target_field]:
                        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                        if match:
                            value = clean_value(match.group(1))
                            result.append({
                                "field": target_field,
                                "value": value
                            })
                            print(f"  ✓ {target_field}: {value[:50]}...")
                            break
            
            if len(result) >= len(target_fields):
                break
    
    return result


def main():
    """تابع اصلی"""
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "OIII.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ فایل PDF یافت نشد: {pdf_path}")
        sys.exit(1)
    
    # استخراج داده‌ها
    try:
        data = extract_ad2_2(pdf_path)
        
        if not data:
            print("❌ هیچ داده‌ای استخراج نشد!")
            sys.exit(1)
        
        # ذخیره در فایل JSON
        output_path = "ad2_2_output.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ استخراج با موفقیت انجام شد!")
        print(f"📁 فایل خروجی: {output_path}")
        print(f"📊 تعداد فیلدهای استخراج شده: {len(data)}")
        print("\n📋 داده‌های استخراج شده:")
        for item in data:
            print(f"  • {item['field']}: {item['value'][:80]}...")
        
    except Exception as e:
        print(f"\n❌ خطا در پردازش: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

