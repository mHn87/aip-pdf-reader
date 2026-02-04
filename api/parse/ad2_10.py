import os
import sys
import json
from http.server import BaseHTTPRequestHandler

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

from parser_ad2_10 import extract_ad2_10

uploaded_pdf_path = os.environ.get('UPLOADED_PDF_PATH')

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global uploaded_pdf_path
        
        pdf_path = uploaded_pdf_path or os.environ.get('UPLOADED_PDF_PATH')
        
        if not pdf_path or not os.path.exists(pdf_path):
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "error": "No PDF uploaded. Please upload a PDF first."
            }).encode())
            return
        
        try:
            data = extract_ad2_10(pdf_path)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "data": data}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "error": str(e)
            }).encode())
