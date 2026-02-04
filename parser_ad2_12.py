#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
پارسر دقیق برای AD 2.12 - RUNWAY PHYSICAL CHARACTERISTICS
این جدول دارای ستون‌های عمودی است و همیشه دو تکه است (6 ستون اول + 6 ستون بعدی)

ساختار جدول:
بخش اول (ستون‌های 1-6):
1. Designations RWY NR
2. TRUE BRG
3. Dimensions of RWY (M)
4. Strength (PCR or PCN) and surface of RWY and SWY
5. THR coordinates THR geoid undulation
6. THR elevation and highest elevation of TDZ of precision APP RWY

بخش دوم (ستون‌های 7-12):
7. Slope of RWY - SWY
8. SWY dimensions (M)
9. CWY dimensions (M)
10. Strip dimensions (M)
11. RESA (M)
12. OFZ
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
    # ضروری: / . ( ) - + % : , x X
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


def extract_ad2_12(pdf_path: str) -> list:
    """
    استخراج دقیق داده‌های AD 2.12 از PDF
    پشتیبانی از جدول‌های چند صفحه‌ای
    
    Returns:
        list: آرایه‌ای از رکوردهای باندها
    """
    result = []
    
    print(f"🔍 در حال جستجوی AD 2.12 در PDF: {pdf_path}")
    
    with pdfplumber.open(pdf_path) as pdf:
        # ابتدا همه صفحات مربوط به AD 2.12 را پیدا می‌کنیم
        ad2_12_pages = []
        ad2_12_started = False
        
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            
            if not text:
                continue
            
            # بررسی شروع AD 2.12
            if "AD 2.12" in text or "AD2.12" in text:
                ad2_12_started = True
                ad2_12_pages.append((page_num, text))
                print(f"✅ صفحه {page_num + 1} پیدا شد: AD 2.12 (شروع)")
            
            # بررسی ادامه جدول در صفحات بعدی
            elif ad2_12_started:
                # اگر به AD 2.13 رسیدیم، پایان AD 2.12
                if "AD 2.13" in text or "AD2.13" in text:
                    # ممکن است بخشی از AD 2.12 در همین صفحه باشد
                    ad2_12_pages.append((page_num, text))
                    print(f"✅ صفحه {page_num + 1} پیدا شد: AD 2.12 (پایان)")
                    break
                
                # بررسی اینکه آیا این صفحه ادامه جدول است
                # معمولاً ادامه جدول شامل داده‌های باند یا header های ستون است
                if is_continuation_page(text):
                    ad2_12_pages.append((page_num, text))
                    print(f"✅ صفحه {page_num + 1} پیدا شد: AD 2.12 (ادامه)")
                else:
                    # اگر صفحه مربوط به AD 2.12 نیست، پایان جدول
                    break
        
        if not ad2_12_pages:
            print("❌ صفحه‌ای برای AD 2.12 پیدا نشد")
            return result
        
        print(f"📄 تعداد صفحات AD 2.12: {len(ad2_12_pages)}")
        
        # ترکیب متن همه صفحات
        combined_text = combine_pages_text(ad2_12_pages)
        
        # استخراج داده‌ها
        result = parse_ad2_12_text(combined_text)
    
    return result


def is_continuation_page(text: str) -> bool:
    """
    بررسی اینکه آیا صفحه ادامه جدول AD 2.12 است
    """
    text_upper = text.upper()
    
    # الگوهای ادامه جدول
    continuation_indicators = [
        # داده‌های باند
        r'\b(11[LRC]|29[LRC]|0[1-9][LRC]|[1-3][0-9][LRC])\b',
        # header های بخش اول
        "DESIGNATIONS",
        "TRUE BRG",
        "DIMENSIONS OF RWY",
        "THR COORDINATES",
        "THR ELEVATION",
        # header های بخش دوم
        "SLOPE OF RWY",
        "SWY DIMENSIONS",
        "CWY DIMENSIONS",
        "STRIP DIMENSION",
        "RESA",
        "OFZ",
        # شماره ستون‌ها
        "1 2 3 4 5 6",
        "7 8 9 10 11 12",
    ]
    
    for indicator in continuation_indicators:
        if indicator.startswith(r'\b'):
            # الگوی regex
            if re.search(indicator, text, re.IGNORECASE):
                return True
        else:
            # متن ساده
            if indicator in text_upper:
                return True
    
    return False


def combine_pages_text(pages: list) -> str:
    """
    ترکیب متن صفحات برای پردازش یکپارچه
    """
    combined_parts = []
    
    for page_num, text in pages:
        # تمیز کردن متن
        text = clean_text_for_parsing(text)
        
        # حذف header و footer صفحات (معمولاً شامل AIP, CIVIL AVIATION و غیره)
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


def parse_ad2_12_text(text: str) -> list:
    """
    Parse دقیق متن AD 2.12 با در نظر گیری ساختار دو تکه
    پشتیبانی از جدول‌های چند صفحه‌ای
    """
    runways_dict = {}  # استفاده از dict برای جلوگیری از تکرار باندها
    
    # تمیز کردن متن از کاراکترهای یونیکد خاص
    text = clean_text_for_parsing(text)
    
    # پیدا کردن بخش AD 2.12
    start_idx = text.find("AD 2.12")
    if start_idx == -1:
        start_idx = 0  # اگر header حذف شده، از ابتدا شروع کن
    
    # پیدا کردن پایان بخش (شروع AD 2.13 یا پایان متن)
    end_idx = text.find("AD 2.13", start_idx)
    if end_idx == -1:
        end_idx = len(text)
    
    ad2_12_text = text[start_idx:end_idx]
    
    # تقسیم متن به خطوط
    lines = ad2_12_text.split('\n')
    
    # پیدا کردن داده‌های بخش اول (باندها با داده‌های ستون 1-6)
    # الگو: باند + TRUE BRG + Dimensions + Strength + Coordinates + THR elevation
    
    # داده‌های هر باند در چند خط متوالی هستند
    runway_data_part1 = []
    
    # الگوی باند: هر باند معتبر (01L-36R)
    # فرمت: 11L 109.63GEO 3646 x 45 720/R/A/W/T 354144.03N THR 3956 FT
    runway_pattern = r'^(\d{2}[LRCM]?)\s+(\d+\.\d+)GEO\s+(\d+\s*x\s*\d+)\s+(\d+/[A-Z]/[A-Z]/[A-Z]/[A-Z])\s+(\d+\.?\d*[NS])\s+THR\s+(\d+)\s*FT'
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # جستجوی الگوی باند در خط
        match = re.match(runway_pattern, line)
        if match:
            rwy_nr = match.group(1)
            true_brg = match.group(2) + " GEO"
            dimensions = match.group(3)
            strength = match.group(4)
            thr_lat = match.group(5)
            thr_elev = "THR " + match.group(6) + " FT"
            
            # خط بعدی: سطح (Concrete/Asphalt) + مختصات طول جغرافیایی
            surface = ""
            thr_lon = ""
            gund = ""
            
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # الگو: Concrete/Asphalt + مختصات
                surface_match = re.match(r'^(Concrete|Asphalt)\s+(\d+\.?\d*[EW])', next_line, re.IGNORECASE)
                if surface_match:
                    surface = surface_match.group(1)
                    thr_lon = surface_match.group(2)
                    i += 1
            
            # خط بعدی: GUND
            if i + 1 < len(lines):
                gund_line = lines[i + 1].strip()
                gund_match = re.match(r'^GUND\s*([+-]?\d+)\s*FT', gund_line, re.IGNORECASE)
                if gund_match:
                    gund = "GUND " + gund_match.group(1) + "FT"
                    i += 1
            
            # ساخت مختصات کامل
            thr_coordinates = f"{thr_lat} {thr_lon} {gund}".strip()
            
            # اضافه کردن سطح به strength
            if surface:
                strength = f"{strength} {surface}"
            
            # اگر این باند قبلاً وجود ندارد، اضافه کن
            if rwy_nr not in runways_dict:
                runways_dict[rwy_nr] = {
                    "Designations RWY NR": rwy_nr,
                    "TRUE BRG": true_brg,
                    "Dimensions of RWY": dimensions,
                    "Strength (PCR or PCN) and surface of RWY and SWY": strength,
                    "THR coordinates THR geoid undulation": thr_coordinates,
                    "THR elevation and highest elevation of TDZ of precision APP RWY": thr_elev,
                }
                runway_data_part1.append(runways_dict[rwy_nr])
                print(f"  ✓ باند {rwy_nr} پیدا شد (بخش 1)")
        
        i += 1
    
    # پیدا کردن داده‌های بخش دوم (ستون‌های 7-12)
    # الگو: Slope + SWY + CWY + Strip + RESA + OFZ
    
    # پیدا کردن شروع بخش دوم (بعد از ستون‌های 7-12)
    part2_start = ad2_12_text.find("Slope of")
    if part2_start == -1:
        part2_start = ad2_12_text.find("7 8 9 10 11 12")
    
    if part2_start != -1:
        part2_text = ad2_12_text[part2_start:]
        part2_lines = part2_text.split('\n')
        
        # الگوی داده‌های بخش دوم
        # هر خط: Slope% + SWY + CWY + Strip + RESA + OFZ
        part2_pattern = r'^(\d+\.?\d*)\s*%\s+(NIL|\d+\s*x\s*\d+)\s+(NIL|\d+\s*x\s*\d+)\s+(NIL|\d+\s*x\s*\d+)\s+(NIL|\d+\s*x\s*\d+)\s+(NIL|[^\s]+)'
        
        runway_idx = 0
        processed_part2 = set()  # برای جلوگیری از پردازش تکراری
        
        for line in part2_lines:
            line = line.strip()
            match = re.match(part2_pattern, line, re.IGNORECASE)
            if match and runway_idx < len(runway_data_part1):
                # بررسی تکراری نبودن
                rwy_nr = runway_data_part1[runway_idx]["Designations RWY NR"]
                if rwy_nr in processed_part2:
                    continue
                
                slope = match.group(1) + "%"
                swy = clean_value(match.group(2))
                cwy = clean_value(match.group(3))
                strip = clean_value(match.group(4))
                resa = clean_value(match.group(5))
                ofz = clean_value(match.group(6))
                
                # اضافه کردن به داده‌های باند
                runway_data_part1[runway_idx]["Slope of RWY - SWY"] = slope
                runway_data_part1[runway_idx]["SWY dimensions"] = swy
                runway_data_part1[runway_idx]["CWY dimensions"] = cwy
                runway_data_part1[runway_idx]["Strip dimensions"] = strip
                runway_data_part1[runway_idx]["RESA"] = resa
                runway_data_part1[runway_idx]["OFZ"] = ofz
                
                processed_part2.add(rwy_nr)
                print(f"  ✓ باند {rwy_nr} پیدا شد (بخش 2)")
                
                runway_idx += 1
    
    # استخراج واحدها از header ها
    # واحدها معمولاً در پرانتز هستند: (M)
    units = extract_units_from_headers(ad2_12_text)
    
    # اضافه کردن واحدها به داده‌ها (Case sensitive)
    for runway in runway_data_part1:
        for field_name, unit in units.items():
            if field_name in runway and runway[field_name] is not None:
                runway[f"{field_name}_unit"] = unit
    
    # مرتب‌سازی فیلدها در ترتیب صحیح
    field_order = [
        "Designations RWY NR",
        "TRUE BRG",
        "Dimensions of RWY",
        "Dimensions of RWY_unit",
        "Strength (PCR or PCN) and surface of RWY and SWY",
        "THR coordinates THR geoid undulation",
        "THR elevation and highest elevation of TDZ of precision APP RWY",
        "Slope of RWY - SWY",
        "SWY dimensions",
        "SWY dimensions_unit",
        "CWY dimensions",
        "CWY dimensions_unit",
        "Strip dimensions",
        "Strip dimensions_unit",
        "RESA",
        "RESA_unit",
        "OFZ",
    ]
    
    sorted_runways = []
    for runway in runway_data_part1:
        sorted_runway = {}
        for field in field_order:
            if field in runway:
                sorted_runway[field] = runway[field]
        # اضافه کردن فیلدهایی که در لیست نیستند
        for field in runway:
            if field not in sorted_runway:
                sorted_runway[field] = runway[field]
        sorted_runways.append(sorted_runway)
    
    return sorted_runways


def extract_units_from_headers(text: str) -> dict:
    """
    استخراج واحدها از header های جدول (Case sensitive)
    """
    units = {}
    
    # الگوهای واحد در header ها
    # جستجو در متن برای یافتن واحدها در پرانتز
    unit_patterns = {
        "Dimensions of RWY": r"RWY\s*\(([A-Za-z]+)\)",
        "SWY dimensions": r"SWY[^\n]*?\(([A-Za-z]+)\)",
        "CWY dimensions": r"CWY[^\n]*?\(([A-Za-z]+)\)",
        "Strip dimensions": r"Strip[^\n]*?\(([A-Za-z]+)\)",
        "RESA": r"RESA[^\n]*?\(([A-Za-z]+)\)",
    }
    
    for field_name, pattern in unit_patterns.items():
        match = re.search(pattern, text)  # Case sensitive
        if match:
            units[field_name] = match.group(1)  # Case sensitive - مثلاً M
    
    # اگر واحدها پیدا نشدند، از مقادیر پیش‌فرض استفاده می‌کنیم
    # بر اساس استاندارد AIP، واحد ابعاد M (متر) است
    default_units = {
        "Dimensions of RWY": "M",
        "SWY dimensions": "M",
        "CWY dimensions": "M",
        "Strip dimensions": "M",
        "RESA": "M",
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
        data = extract_ad2_12(pdf_path)
        
        if not data:
            print("❌ هیچ داده‌ای استخراج نشد!")
            sys.exit(1)
        
        # ذخیره در فایل JSON
        output_path = "ad2_12_output.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ استخراج با موفقیت انجام شد!")
        print(f"📁 فایل خروجی: {output_path}")
        print(f"📊 تعداد باندهای استخراج شده: {len(data)}")
        print("\n📋 داده‌های استخراج شده:")
        
        for i, runway in enumerate(data, 1):
            print(f"\n  باند {i}: {runway.get('Designations RWY NR', 'N/A')}")
            for key, value in runway.items():
                if key != "Designations RWY NR":
                    display_value = str(value)[:70] + "..." if len(str(value)) > 70 else value
                    print(f"    • {key}: {display_value}")
        
    except Exception as e:
        print(f"\n❌ خطا در پردازش: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
