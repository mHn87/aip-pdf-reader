#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
پارسر دقیق برای AD 2.10 - AERODROME OBSTACLES
فقط بخش In approach / TKOF areas

استفاده از extract_tables برای استخراج دقیق داده‌ها
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
    # ضروری: / . ( ) - + % : ,
    text = re.sub(r'[^\w\s\n/.()%:,+-]', '', text)
    
    return text


def clean_value(text: str):
    """تمیز کردن مقدار برای خروجی JSON"""
    if not text:
        return None
    
    text = deep_clean_text(text).strip()
    
    if text.upper() == "NIL":
        return None
    
    # تمیز کردن فاصله‌های اضافی
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text if text else None


def parse_rwy_cell(cell_text: str) -> list:
    """
    Parse cell مربوط به RWY و برگرداندن لیست کلیدها (بدون تکرار)
    
    مثال:
    - "11R / APCH\n29L / TKOF" → ["11R / APCH", "29L / TKOF"]
    - "11L/R / APCH\n29L/R / TKOF" → ["11L / APCH", "11R / APCH", "29L / TKOF", "29R / TKOF"]
    """
    if not cell_text:
        return []
    
    # تمیز کردن عمیق قبل از پردازش
    cell_text = deep_clean_text(cell_text)
    
    keys = set()  # استفاده از set برای جلوگیری از تکرار
    
    # جدا کردن خطوط
    lines = cell_text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # الگو: "11R / APCH" یا "11L/R / APCH"
        match = re.match(r'^(\d{2})([LRC]?(?:/[LRC])?)\s*/\s*(APCH|TKOF)', line, re.IGNORECASE)
        if not match:
            continue
        
        rwy_num = match.group(1)
        rwy_suffix = match.group(2).upper() if match.group(2) else ""
        rwy_type = match.group(3).upper()
        
        if not rwy_suffix:
            # مثلاً "11 / APCH" → هم 11L و هم 11R
            keys.add(f"{rwy_num}L / {rwy_type}")
            keys.add(f"{rwy_num}R / {rwy_type}")
        elif "/" in rwy_suffix:
            # مثلاً "L/R" → هم L و هم R
            parts = rwy_suffix.replace("/", "")
            for p in parts:
                keys.add(f"{rwy_num}{p} / {rwy_type}")
        else:
            # مثلاً "11R / APCH"
            keys.add(f"{rwy_num}{rwy_suffix} / {rwy_type}")
    
    return list(keys)


def parse_obstacle_cell(cell_text: str) -> dict:
    """
    Parse cell مربوط به Obstacle و برگرداندن type, elevation, markings
    
    مثال:
    - "DVOR/DME antenna\n4010 FT AMSL\nLGTD"
    - "LOC 29L\nantenna\n3994 FT AMSL\nLGTD"
    """
    if not cell_text:
        return {"obstacle_type": None, "elevation": None, "markings": None}
    
    # تمیز کردن عمیق قبل از پردازش
    cell_text = deep_clean_text(cell_text)
    
    lines = cell_text.split('\n')
    
    obstacle_parts = []
    elevation = None
    markings = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # بررسی LGTD/NIL
        if line.upper() in ['LGTD', 'NIL']:
            markings = line.upper()
            continue
        
        # بررسی elevation
        elev_match = re.search(r'(\d+)\s*FT\s*(AMSL|AGL)', line, re.IGNORECASE)
        if elev_match:
            elevation = f"{elev_match.group(1)} FT {elev_match.group(2).upper()}"
            # حذف elevation از خط و اضافه کردن باقیمانده به obstacle
            remaining = re.sub(r'\d+\s*FT\s*(?:AMSL|AGL)', '', line, flags=re.IGNORECASE).strip()
            if remaining:
                obstacle_parts.append(remaining)
            continue
        
        # بقیه خطوط = obstacle type
        obstacle_parts.append(line)
    
    obstacle_type = ' '.join(obstacle_parts).strip() if obstacle_parts else None
    
    # تمیز کردن obstacle_type
    if obstacle_type:
        obstacle_type = re.sub(r'[^\w\s/()-]', '', obstacle_type)
        obstacle_type = re.sub(r'\s+', ' ', obstacle_type).strip()
    
    return {
        "obstacle_type": obstacle_type,
        "elevation": elevation,
        "markings": markings
    }


def parse_coordinates_cell(cell_text: str) -> str:
    """
    Parse cell مربوط به Coordinates
    
    مثال:
    - "354149.1N\n0511701.6E" → "354149.1N 0511701.6E"
    """
    if not cell_text:
        return None
    
    # تمیز کردن عمیق قبل از پردازش
    cell_text = deep_clean_text(cell_text)
    
    # پیدا کردن lat و lon
    lat_match = re.search(r'(\d{6}\.?\d*[NS])', cell_text)
    lon_match = re.search(r'(0\d{6}\.?\d*[EW])', cell_text)
    
    if lat_match and lon_match:
        return f"{lat_match.group(1)} {lon_match.group(1)}"
    elif lat_match:
        return lat_match.group(1)
    elif lon_match:
        return lon_match.group(1)
    
    return None


def extract_ad2_10(pdf_path: str) -> dict:
    """استخراج داده‌های AD 2.10 با استفاده از extract_tables"""
    
    result = {}
    
    print(f"🔍 در حال جستجوی AD 2.10 در PDF: {pdf_path}")
    
    with pdfplumber.open(pdf_path) as pdf:
        ad2_10_pages = []
        
        # پیدا کردن صفحات AD 2.10
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            
            if not text:
                continue
            
            if "AD 2.10" in text or "AERODROME OBSTACLES" in text:
                ad2_10_pages.append(page)
                print(f"✅ صفحه {page_num + 1} پیدا شد: AD 2.10")
            elif ad2_10_pages:
                if "AD 2.11" in text:
                    break
                # بررسی ادامه جدول
                if any(ind in text.upper() for ind in ["FT AMSL", "FT AGL", "/ APCH", "/ TKOF"]):
                    ad2_10_pages.append(page)
                    print(f"✅ صفحه {page_num + 1} پیدا شد: AD 2.10 (ادامه)")
                else:
                    break
        
        if not ad2_10_pages:
            print("❌ صفحه‌ای برای AD 2.10 پیدا نشد")
            return result
        
        print(f"📄 تعداد صفحات AD 2.10: {len(ad2_10_pages)}")
        
        # استخراج جداول از همه صفحات
        all_rows = []
        last_rwy_cell = None  # برای سطرهایی که cell اول None است
        
        for page in ad2_10_pages:
            tables = page.extract_tables()
            
            for table in tables:
                if not table:
                    continue
                
                for row in table:
                    if not row or len(row) < 3:
                        continue
                    
                    first_cell = str(row[0] or "").strip()
                    
                    # بررسی header row
                    if first_cell in ['In approach / TKOF areas', 'RWY/Area affected', '1', 'a']:
                        continue
                    
                    # بررسی سطر خالی
                    obstacle_cell = str(row[1] or "").strip() if len(row) > 1 else ""
                    coords_cell = str(row[2] or "").strip() if len(row) > 2 else ""
                    
                    if not obstacle_cell and not coords_cell:
                        continue
                    
                    # اگر cell اول None یا خالی است، از آخرین RWY استفاده کن
                    if not first_cell and last_rwy_cell:
                        row = list(row)
                        row[0] = last_rwy_cell
                    elif first_cell and re.search(r'\d{2}[LRC]?\s*/\s*(?:APCH|TKOF)', first_cell, re.IGNORECASE):
                        last_rwy_cell = first_cell
                    else:
                        continue
                    
                    all_rows.append(row)
        
        print(f"📊 تعداد سطرهای جدول: {len(all_rows)}")
        
        # پردازش هر سطر
        for row in all_rows:
            # ستون 0: RWY/Area affected
            # ستون 1: Obstacle type\nElevation/ HGT\nMarkings/LGT (approach)
            # ستون 2: Coordinates (approach)
            # ستون 3-5: مربوط به circling (نادیده گرفته می‌شود)
            
            rwy_cell = row[0] if len(row) > 0 else None
            obstacle_cell = row[1] if len(row) > 1 else None
            coords_cell = row[2] if len(row) > 2 else None
            
            # Parse RWY
            rwy_keys = parse_rwy_cell(rwy_cell)
            if not rwy_keys:
                continue
            
            # Parse Obstacle
            obstacle_info = parse_obstacle_cell(obstacle_cell)
            
            # Parse Coordinates
            coordinates = parse_coordinates_cell(coords_cell)
            
            # ساخت فیلد ترکیبی
            combined_parts = []
            if obstacle_info["obstacle_type"]:
                combined_parts.append(obstacle_info["obstacle_type"])
            if obstacle_info["elevation"]:
                combined_parts.append(obstacle_info["elevation"])
            if obstacle_info["markings"]:
                combined_parts.append(obstacle_info["markings"])
            
            combined_value = ' '.join(combined_parts) if combined_parts else None
            
            # ساخت رکورد
            obstacle_data = {
                "Coordinates": coordinates,
                "Obstacle type Elevation/HGT Markings/LGT": combined_value
            }
            
            # ذخیره در همه کلیدهای مربوطه
            for key in rwy_keys:
                if key not in result:
                    result[key] = []
                result[key].append(obstacle_data)
    
    # شمارش
    total_entries = sum(len(v) for v in result.values())
    print(f"  ✓ {len(result)} کلید RWY پیدا شد")
    print(f"  ✓ {total_entries} مانع ذخیره شد")
    
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
    
    try:
        data = extract_ad2_10(pdf_path)
        
        if not data:
            print("❌ هیچ داده‌ای استخراج نشد!")
            sys.exit(1)
        
        output_path = "ad2_10_output.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ استخراج با موفقیت انجام شد!")
        print(f"📁 فایل خروجی: {output_path}")
        
        print("\n📋 نمونه داده‌ها:")
        for key in list(data.keys())[:6]:
            print(f"\n  📌 {key} ({len(data[key])} مانع):")
            for i, obs in enumerate(data[key][:3], 1):
                coords = obs.get('Coordinates') or 'N/A'
                info = obs.get('Obstacle type Elevation/HGT Markings/LGT') or 'N/A'
                print(f"    {i}. Coords: {coords}")
                print(f"       Info: {info}")
            if len(data[key]) > 3:
                print(f"    ... و {len(data[key]) - 3} مورد دیگر")
        
    except Exception as e:
        print(f"\n❌ خطا در پردازش: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
