import os
import sys
import json
from http.server import BaseHTTPRequestHandler

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

def _get_data(pdf_path: str):
    """PDF → Unstructured elements → AD 2.2."""
    from lib.pdf_to_elements import pdf_path_to_elements
    from ad2_2_from_elements import extract_ad2_2_from_elements
    elements = pdf_path_to_elements(pdf_path)
    return extract_ad2_2_from_elements(elements)

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": "No file data provided"}).encode())
            return
        try:
            body = json.loads(self.rfile.read(content_length).decode('utf-8'))
            file_data_base64 = body.get('fileData')
        except Exception:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": "Invalid request body"}).encode())
            return
        if not file_data_base64:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": "No PDF uploaded. Please upload a PDF first."}).encode())
            return
        import base64
        import uuid
        try:
            file_data = base64.b64decode(file_data_base64)
            pdf_path = os.path.join('/tmp', f"aip_parse_{uuid.uuid4().hex[:8]}.pdf")
            with open(pdf_path, 'wb') as f:
                f.write(file_data)
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode())
            return
        try:
            data = _get_data(pdf_path)
            try:
                os.remove(pdf_path)
            except Exception:
                pass
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "data": data}).encode())
        except Exception as e:
            try:
                os.remove(pdf_path)
            except Exception:
                pass
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode())
