#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
پارسر دقیق برای AD 2.1 - AERODROME LOCATION INDICATOR AND NAME
"""

import json
import re
import sys
from pathlib import Path
import pdfplumber


def deep_clean_text(text: str) -> str:
    """
    تمیز کردن عمیق متن - حذف همه کاراکترهای غیرعادی
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
    
    return text


def clean_value(text: str):
    """تمیز کردن مقدار برای خروجی JSON"""
    if not text:
        return None
    
    text = deep_clean_text(text).strip()
    
    if text.upper() == "NIL":
        return None
    
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text if text else None


def extract_ad2_1(pdf_path: str) -> dict:
    """
    استخراج دقیق داده‌های AD 2.1 از PDF
    
    Returns:
        dict: شامل name, country (city), aip
    """
    result = {
        "name": None,
        "country": None,
        "aip": None
    }
    
    print(f"🔍 در حال جستجوی AD 2.1 در PDF: {pdf_path}")
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages[:5]):  # فقط 5 صفحه اول
            text = page.extract_text()
            
            if not text:
                continue
            
            # تمیز کردن متن
            text = deep_clean_text(text)
            
            # جستجوی AD 2.1
            if "AD 2.1" not in text and "AERODROME LOCATION INDICATOR" not in text:
                continue
            
            print(f"✅ صفحه {page_num + 1} پیدا شد: AD 2.1")
            
            # الگوی استخراج: ICAO_CODE - CITY / Airport Name
            # مثال: OIII - TEHRAN / Mehrabad International
            
            # الگوی دقیق برای خط AD 2.1
            # OIII - TEHRAN / Mehrabad International
            pattern_main = r'([A-Z]{4})\s*-\s*([A-Z]+)\s*/\s*([A-Za-z]+)\s+International'
            
            match = re.search(pattern_main, text)
            if match:
                icao_code = match.group(1).upper().strip()
                city = match.group(2).strip().title()
                airport_name = match.group(3).strip() + " International"
                
                result["name"] = clean_value(icao_code)
                result["country"] = clean_value(city)
                result["aip"] = clean_value(airport_name)
                
                print(f"  ✓ name: {result['name']}")
                print(f"  ✓ country: {result['country']}")
                print(f"  ✓ aip: {result['aip']}")
                
                return result
            
            # اگر الگوها کار نکردند، روش دیگر
            # جستجوی مستقیم ICAO code از header
            header_match = re.search(r'AIP\s+AD\s+\d+-\d+\s+([A-Z]{4})', text)
            if header_match:
                icao_code = header_match.group(1)
                
                # جستجوی city و name
                name_match = re.search(rf'{icao_code}\s*-\s*([A-Z][A-Za-z]+)\s*/\s*([A-Za-z\s]+?)(?:International|INTL|\n)', text)
                if name_match:
                    city = name_match.group(1).strip().title()
                    airport_name = name_match.group(2).strip()
                    airport_name = re.sub(r'\s+', ' ', airport_name).strip()
                    if 'international' not in airport_name.lower():
                        airport_name = airport_name + " International"
                    
                    result["name"] = clean_value(icao_code)
                    result["country"] = clean_value(city)
                    result["aip"] = clean_value(airport_name)
                    
                    print(f"  ✓ name: {result['name']}")
                    print(f"  ✓ country: {result['country']}")
                    print(f"  ✓ aip: {result['aip']}")
                    
                    return result
            
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
    
    try:
        data = extract_ad2_1(pdf_path)
        
        if not data or not data.get("name"):
            print("❌ هیچ داده‌ای استخراج نشد!")
            sys.exit(1)
        
        # ذخیره در فایل JSON
        output_path = "ad2_1_output.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ استخراج با موفقیت انجام شد!")
        print(f"📁 فایل خروجی: {output_path}")
        print(f"\n📋 داده‌های استخراج شده:")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"\n❌ خطا در پردازش: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
