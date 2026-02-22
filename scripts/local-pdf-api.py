#!/usr/bin/env python3
"""
Local API server for PDF processing using minerU
"""
import json
import sys
import os
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

# Add lib to path
ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT / "lib"))

from pdf_to_elements import pdf_path_to_elements

class PDFHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path != '/api/pdf-to-elements':
            self.send_response(404)
            self.end_headers()
            return

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
                self.wfile.write(json.dumps({"error": "pdfUrl required"}).encode())
                return

            print(f"Processing PDF: {pdf_url}")
            tables = pdf_path_to_elements(pdf_url)
            
            response = {"success": True, "tables": tables}
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"Error: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

def run_server():
    server = HTTPServer(('localhost', 8001), PDFHandler)
    print("PDF API server running on http://localhost:8001")
    print("Endpoint: POST http://localhost:8001/api/pdf-to-elements")
    server.serve_forever()

if __name__ == '__main__':
    run_server()