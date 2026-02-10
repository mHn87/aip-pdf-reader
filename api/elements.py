"""
یک بار PDF را به Unstructured می‌فرستیم و elements را برمی‌گردانیم.
بقیهٔ پارس‌ها (AD 2.1, 2.12, 2.13, ...) روی همین elements و فقط وقتی viewport روی آن بخش است انجام می‌شود.
"""
import os
import sys
import json
import base64
import uuid
from http.server import BaseHTTPRequestHandler

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)


def _get_elements(pdf_path: str):
    from lib.pdf_to_elements import pdf_path_to_elements
    return pdf_path_to_elements(pdf_path)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self._send_json(400, {"success": False, "error": "No file data provided"})
            return
        try:
            body = json.loads(self.rfile.read(content_length).decode("utf-8"))
            file_data_base64 = body.get("fileData")
        except Exception:
            self._send_json(400, {"success": False, "error": "Invalid request body"})
            return
        if not file_data_base64:
            self._send_json(400, {"success": False, "error": "No PDF uploaded. Please upload a PDF first."})
            return
        try:
            file_data = base64.b64decode(file_data_base64)
            pdf_path = os.path.join("/tmp", f"aip_elements_{uuid.uuid4().hex[:8]}.pdf")
            with open(pdf_path, "wb") as f:
                f.write(file_data)
        except Exception as e:
            self._send_json(500, {"success": False, "error": str(e)})
            return
        try:
            elements = _get_elements(pdf_path)
            try:
                os.remove(pdf_path)
            except Exception:
                pass
            self._send_json(200, {"success": True, "elements": elements})
        except Exception as e:
            try:
                os.remove(pdf_path)
            except Exception:
                pass
            self._send_json(500, {"success": False, "error": str(e)})

    def _send_json(self, status: int, obj: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())
