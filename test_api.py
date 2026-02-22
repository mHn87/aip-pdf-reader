#!/usr/bin/env python3
"""
تست محلی برای API minerU
"""
import json
import sys
from pathlib import Path

# Add lib to path
ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT / "lib"))

from pdf_to_elements import pdf_path_to_elements

def test_api():
    # Test URL - replace with actual PDF URL
    test_url = "https://example.com/test.pdf"
    
    try:
        print(f"Testing minerU API with URL: {test_url}")
        result = pdf_path_to_elements(test_url)
        print("Success!")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()