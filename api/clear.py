import os
import json
from http.server import BaseHTTPRequestHandler

uploaded_pdf_path = os.environ.get('UPLOADED_PDF_PATH')

class handler(BaseHTTPRequestHandler):
    def do_DELETE(self):
        global uploaded_pdf_path
        
        pdf_path = uploaded_pdf_path or os.environ.get('UPLOADED_PDF_PATH')
        
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except:
                pass
        
        # Clear environment variable
        if 'UPLOADED_PDF_PATH' in os.environ:
            del os.environ['UPLOADED_PDF_PATH']
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({
            "success": True,
            "message": "Upload cleared"
        }).encode())
