#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
پارسر دقیق برای AD 2.13 - DECLARED DISTANCES
این جدول ممکن است چند صفحه‌ای باشد و هر باند می‌تواند چندین ردیف داشته باشد

ساختار جدول:
1. RWY Designator - شماره باند
2. TORA (M) - Take-Off Run Available
3. TODA (M) - Take-Off Distance Available
4. ASDA (M) - Accelerate-Stop Distance Available
5. LDA (M) - Landing Distance Available
6. Remarks - توضیحات

خروجی: داده‌ها بر اساس باند cluster می‌شوند
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
    text = re.sub(r'[^\w\s\n/.()%:,x+-]', '', text, flags=re.IGNORECASE)
    
    return text


def clean_value(text: str):
    """تمیز کردن مقدار برای خروجی JSON - Case sensitive"""
    if not text:
        return None
    
    text = deep_clean_text(text).strip()
    
    # تبدیل NIL به None (case insensitive)
    if text.upper() == "NIL":
        return None
    
    # تمیز کردن فاصله‌های اضافی
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text if text else None


def clean_text_for_parsing(text: str) -> str:
    """تمیز کردن متن برای پارسینگ"""
    return deep_clean_text(text)


def extract_ad2_13(pdf_path: str) -> list:
    """
    استخراج دقیق داده‌های AD 2.13 از PDF
    پشتیبانی از جدول‌های چند صفحه‌ای
    
    Returns:
        list: آرایه‌ای از رکوردهای باندها با cluster شده
    """
    result = []
    
    print(f"🔍 در حال جستجوی AD 2.13 در PDF: {pdf_path}")
    
    with pdfplumber.open(pdf_path) as pdf:
        # پیدا کردن همه صفحات مربوط به AD 2.13
        ad2_13_pages = []
        ad2_13_started = False
        
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            
            if not text:
                continue
            
            # بررسی شروع AD 2.13
            if "AD 2.13" in text or "AD2.13" in text:
                ad2_13_started = True
                ad2_13_pages.append((page_num, text))
                print(f"✅ صفحه {page_num + 1} پیدا شد: AD 2.13 (شروع)")
            
            # بررسی ادامه جدول در صفحات بعدی
            elif ad2_13_started:
                # اگر به AD 2.14 یا بخش دیگری رسیدیم، پایان
                if "AD 2.14" in text or "AD2.14" in text:
                    # ممکن است بخشی از AD 2.13 در همین صفحه باشد
                    ad2_13_pages.append((page_num, text))
                    print(f"✅ صفحه {page_num + 1} پیدا شد: AD 2.13 (پایان)")
                    break
                
                # بررسی ادامه جدول
                if is_continuation_page(text):
                    ad2_13_pages.append((page_num, text))
                    print(f"✅ صفحه {page_num + 1} پیدا شد: AD 2.13 (ادامه)")
                else:
                    break
        
        if not ad2_13_pages:
            print("❌ صفحه‌ای برای AD 2.13 پیدا نشد")
            return result
        
        print(f"📄 تعداد صفحات AD 2.13: {len(ad2_13_pages)}")
        
        # ترکیب متن همه صفحات
        combined_text = combine_pages_text(ad2_13_pages)
        
        # استخراج داده‌ها
        result = parse_ad2_13_text(combined_text)
    
    return result


def is_continuation_page(text: str) -> bool:
    """بررسی اینکه آیا صفحه ادامه جدول AD 2.13 است"""
    text_upper = text.upper()
    
    # الگوهای ادامه جدول
    continuation_indicators = [
        # داده‌های باند
        r'\b(\d{2}[LRCM]?)\b',
        # header های جدول
        "RWY",
        "DESIGNATOR",
        "TORA",
        "TODA",
        "ASDA",
        "LDA",
        "REMARKS",
        "DECLARED DISTANCES",
    ]
    
    for indicator in continuation_indicators:
        if indicator.startswith(r'\b'):
            if re.search(indicator, text, re.IGNORECASE):
                return True
        else:
            if indicator in text_upper:
                return True
    
    return False


def combine_pages_text(pages: list) -> str:
    """ترکیب متن صفحات"""
    combined_parts = []
    
    for page_num, text in pages:
        text = clean_text_for_parsing(text)
        
        # حذف header و footer
        lines = text.split('\n')
        filtered_lines = []
        
        for line in lines:
            line_upper = line.upper().strip()
            
            # حذف header/footer
            if any(skip in line_upper for skip in [
                "CIVIL AVIATION ORGANIZATION",
                "AIRAC AMDT",
                "AIP",
                "ISLAMIC REPUBLIC OF IRAN",
            ]):
                continue
            
            # حذف شماره صفحه
            if re.match(r'^AD\s*2-\d+\s*OIII', line_upper):
                continue
            if re.match(r'^WEF\s+\d+\s+\w+\s+\d+', line_upper):
                continue
            
            filtered_lines.append(line)
        
        combined_parts.append('\n'.join(filtered_lines))
    
    return '\n'.join(combined_parts)


def parse_ad2_13_text(text: str) -> list:
    """
    Parse دقیق متن AD 2.13
    خروجی: لیست باندها با entries برای هر باند
    """
    runways_dict = {}  # کلید: شماره باند، مقدار: لیست entries
    
    text = clean_text_for_parsing(text)
    
    # پیدا کردن بخش AD 2.13
    start_idx = text.find("AD 2.13")
    if start_idx == -1:
        start_idx = 0
    
    # پیدا کردن پایان بخش
    end_idx = text.find("AD 2.14", start_idx)
    if end_idx == -1:
        end_idx = len(text)
    
    ad2_13_text = text[start_idx:end_idx]
    
    # استخراج واحدها از header
    units = extract_units_from_headers(ad2_13_text)
    
    # تقسیم به خطوط
    lines = ad2_13_text.split('\n')
    
    # الگوی ردیف داده:
    # RWY_NR TORA TODA ASDA LDA [Remarks]
    # مثال: 11L 3646 3646 3646 2796 NIL
    # یا: 29L 3640 3640 3640 NIL Take-off from intersection with U
    
    # الگوی اصلی: شماره باند + 4 عدد + (NIL یا توضیحات)
    row_pattern = r'^(\d{2}[LRCM]?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+|NIL)\s*(.*?)$'
    
    # الگوی ردیف بدون شماره باند (ادامه باند قبلی)
    # مثال: 3544 3544 3544 NIL Take-off from intersection with A2
    continuation_pattern = r'^(\d+)\s+(\d+)\s+(\d+)\s+(\d+|NIL)\s*(.*?)$'
    
    current_rwy = None
    
    for line in lines:
        line = line.strip()
        
        if not line:
            continue
        
        # بررسی ردیف با شماره باند
        match = re.match(row_pattern, line, re.IGNORECASE)
        if match:
            rwy_nr = match.group(1).upper()
            tora = clean_value(match.group(2))
            toda = clean_value(match.group(3))
            asda = clean_value(match.group(4))
            lda = clean_value(match.group(5))
            remarks = clean_value(match.group(6)) if match.group(6) else None
            
            current_rwy = rwy_nr
            
            # ساخت entry
            entry = {
                "TORA": tora,
                "TODA": toda,
                "ASDA": asda,
                "LDA": lda,
                "Remarks": remarks,
            }
            
            # اضافه کردن واحدها
            if tora is not None:
                entry["TORA_unit"] = units.get("TORA", "M")
            if toda is not None:
                entry["TODA_unit"] = units.get("TODA", "M")
            if asda is not None:
                entry["ASDA_unit"] = units.get("ASDA", "M")
            if lda is not None:
                entry["LDA_unit"] = units.get("LDA", "M")
            
            # اضافه کردن به dict
            if rwy_nr not in runways_dict:
                runways_dict[rwy_nr] = []
            runways_dict[rwy_nr].append(entry)
            
            print(f"  ✓ باند {rwy_nr} پیدا شد")
            continue
        
        # بررسی ردیف ادامه (بدون شماره باند)
        if current_rwy:
            cont_match = re.match(continuation_pattern, line, re.IGNORECASE)
            if cont_match:
                tora = clean_value(cont_match.group(1))
                toda = clean_value(cont_match.group(2))
                asda = clean_value(cont_match.group(3))
                lda = clean_value(cont_match.group(4))
                remarks = clean_value(cont_match.group(5)) if cont_match.group(5) else None
                
                entry = {
                    "TORA": tora,
                    "TODA": toda,
                    "ASDA": asda,
                    "LDA": lda,
                    "Remarks": remarks,
                }
                
                # اضافه کردن واحدها
                if tora is not None:
                    entry["TORA_unit"] = units.get("TORA", "M")
                if toda is not None:
                    entry["TODA_unit"] = units.get("TODA", "M")
                if asda is not None:
                    entry["ASDA_unit"] = units.get("ASDA", "M")
                if lda is not None:
                    entry["LDA_unit"] = units.get("LDA", "M")
                
                runways_dict[current_rwy].append(entry)
                print(f"  ✓ ادامه باند {current_rwy} پیدا شد")
    
    # تبدیل به لیست خروجی با ترتیب صحیح
    result = []
    
    # مرتب‌سازی باندها
    sorted_rwys = sorted(runways_dict.keys(), key=lambda x: (int(re.search(r'\d+', x).group()), x))
    
    for rwy_nr in sorted_rwys:
        entries = runways_dict[rwy_nr]
        
        # مرتب کردن فیلدها در هر entry
        ordered_entries = []
        for entry in entries:
            ordered_entry = {}
            field_order = ["TORA", "TORA_unit", "TODA", "TODA_unit", 
                          "ASDA", "ASDA_unit", "LDA", "LDA_unit", "Remarks"]
            
            for field in field_order:
                if field in entry:
                    ordered_entry[field] = entry[field]
            
            ordered_entries.append(ordered_entry)
        
        result.append({
            "RWY Designator": rwy_nr,
            "entries": ordered_entries
        })
    
    return result


def extract_units_from_headers(text: str) -> dict:
    """استخراج واحدها از header های جدول (Case sensitive)"""
    units = {}
    
    # الگوهای واحد
    unit_patterns = {
        "TORA": r"TORA\s*\(([A-Za-z]+)\)",
        "TODA": r"TODA\s*\(([A-Za-z]+)\)",
        "ASDA": r"ASDA\s*\(([A-Za-z]+)\)",
        "LDA": r"LDA\s*\(([A-Za-z]+)\)",
    }
    
    for field_name, pattern in unit_patterns.items():
        match = re.search(pattern, text)
        if match:
            units[field_name] = match.group(1)
    
    # مقادیر پیش‌فرض
    default_units = {
        "TORA": "M",
        "TODA": "M",
        "ASDA": "M",
        "LDA": "M",
    }
    
    for field_name, default_unit in default_units.items():
        if field_name not in units:
            units[field_name] = default_unit
    
    return units


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
        data = extract_ad2_13(pdf_path)
        
        if not data:
            print("❌ هیچ داده‌ای استخراج نشد!")
            sys.exit(1)
        
        # ذخیره در فایل JSON
        output_path = "ad2_13_output.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ استخراج با موفقیت انجام شد!")
        print(f"📁 فایل خروجی: {output_path}")
        print(f"📊 تعداد باندهای استخراج شده: {len(data)}")
        
        # نمایش خلاصه
        total_entries = sum(len(rwy['entries']) for rwy in data)
        print(f"📋 مجموع entries: {total_entries}")
        
        print("\n📋 داده‌های استخراج شده:")
        for rwy in data:
            print(f"\n  باند {rwy['RWY Designator']} ({len(rwy['entries'])} entry):")
            for i, entry in enumerate(rwy['entries'], 1):
                remarks = entry.get('Remarks')
                remarks_display = "null" if remarks is None else (remarks[:40] + "..." if len(remarks) > 40 else remarks)
                tora = entry['TORA'] if entry['TORA'] is not None else "null"
                toda = entry['TODA'] if entry['TODA'] is not None else "null"
                asda = entry['ASDA'] if entry['ASDA'] is not None else "null"
                lda = entry['LDA'] if entry['LDA'] is not None else "null"
                print(f"    {i}. TORA={tora}, TODA={toda}, ASDA={asda}, LDA={lda}, Remarks={remarks_display}")
        
    except Exception as e:
        print(f"\n❌ خطا در پردازش: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
