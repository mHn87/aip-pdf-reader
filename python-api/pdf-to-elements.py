import json
import sys
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs

# Add lib to Python path
ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT / "lib"))

try:
    from pdf_to_elements import pdf_path_to_elements
except ImportError as e:
    print(f"Import error: {e}")

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data.decode('utf-8'))
            
            pdf_url = body.get('pdfUrl')
            if not pdf_url:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "pdfUrl نامعتبر یا موجود نیست"}).encode())
                return

            # Process PDF
            tables = pdf_path_to_elements(pdf_url)
            
            response = {"success": True, "tables": tables}
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())