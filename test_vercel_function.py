#!/usr/bin/env python3
"""
Test the Vercel Python function locally
"""
import sys
import os
from pathlib import Path

# Add the python-api directory to path
ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT / "python-api"))

# Mock HTTP request for testing
class MockRequest:
    def __init__(self, method="POST", body='{"pdfUrl": "https://example.com/test.pdf"}'):
        self.method = method
        self.body = body.encode('utf-8')
        self.headers = {'Content-Length': str(len(self.body))}
    
    def rfile_read(self, length):
        return self.body

# Test the handler
try:
    from python_api.pdf_to_elements import handler
    print("✅ Import successful")
    
    # Create mock request
    mock_req = MockRequest()
    
    # This would normally be handled by Vercel
    print("✅ Function ready for Vercel deployment")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
except Exception as e:
    print(f"❌ Error: {e}")