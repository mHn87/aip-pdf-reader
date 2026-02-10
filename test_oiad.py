#!/usr/bin/env python3
"""تست پارس OIAD.pdf با pdf_to_elements و استخراج AD 2.1, 2.12, 2.13."""
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))

# بارگذاری .env در صورت وجود (برای UNSTRUCTURED_API_KEY)
_env_file = root / ".env"
if _env_file.exists():
    for line in _env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            key = k.strip()
            val = v.strip().strip("'\"").strip()
            if key and val:
                os.environ.setdefault(key, val)
else:
    try:
        from dotenv import load_dotenv
        load_dotenv(root / ".env")
    except ImportError:
        pass

def main():
    pdf_path = root / "OIAD.pdf"
    if not pdf_path.exists():
        print(f"❌ فایل یافت نشد: {pdf_path}")
        return 1

    print("📄 در حال خواندن PDF با pdf_path_to_elements...")
    if not os.environ.get("UNSTRUCTURED_API_KEY"):
        print("   (برای تست با API: UNSTRUCTURED_API_KEY را در .env یا env تنظیم کن)")
    try:
        from lib.pdf_to_elements import pdf_path_to_elements
        elements = pdf_path_to_elements(str(pdf_path))
        print(f"✅ تعداد elements: {len(elements)}")
    except Exception as e:
        print(f"❌ خطا در خواندن PDF: {e}")
        return 1

    # AD 2.1
    print("\n--- AD 2.1 ---")
    try:
        from ad2_1_from_elements import extract_ad2_1_from_elements
        ad2_1 = extract_ad2_1_from_elements(elements)
        print(f"  name: {ad2_1.get('name')}")
        print(f"  country: {ad2_1.get('country')}")
        print(f"  aip: {ad2_1.get('aip')}")
    except Exception as e:
        print(f"  خطا: {e}")

    # AD 2.12
    print("\n--- AD 2.12 ---")
    try:
        from ad2_12_from_elements import extract_ad2_12_from_elements
        runways = extract_ad2_12_from_elements(elements)
        print(f"  تعداد باند: {len(runways)}")
        for r in runways[:3]:
            print(f"    - {r.get('Designations')}: {r.get('Dimensions of RWY')}")
    except Exception as e:
        print(f"  خطا: {e}")

    # AD 2.13
    print("\n--- AD 2.13 ---")
    try:
        from ad2_13_from_elements import extract_ad2_13_from_elements
        runways13 = extract_ad2_13_from_elements(elements)
        print(f"  تعداد باند: {len(runways13)}")
        for r in runways13[:3]:
            print(f"    - {r.get('RWY Designator')}: {len(r.get('entries', []))} entry")
    except Exception as e:
        print(f"  خطا: {e}")

    print("\n✅ تست تمام شد.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
