import os
import sys
import json
from http.server import BaseHTTPRequestHandler

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

def _get_data_from_pdf(pdf_path: str):
    from lib.pdf_to_elements import pdf_path_to_elements
    from ad2_12_from_elements import extract_ad2_12_from_elements
    elements = pdf_path_to_elements(pdf_path)
    return extract_ad2_12_from_elements(elements)


def _get_data_from_elements(elements):
    from ad2_12_from_elements import extract_ad2_12_from_elements
    return extract_ad2_12_from_elements(elements)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self._send(400, {"success": False, "error": "No body"})
            return
        try:
            body = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except Exception:
            self._send(400, {"success": False, "error": "Invalid request body"})
            return
        el = body.get("elements")
        if isinstance(el, list):
            try:
                data = _get_data_from_elements(el)
                self._send(200, {"success": True, "data": data})
            except Exception as e:
                self._send(500, {"success": False, "error": str(e)})
            return
        file_data_base64 = body.get("fileData")
        if not file_data_base64:
            self._send(400, {"success": False, "error": "No fileData or elements provided."})
            return
        import base64
        import uuid
        try:
            file_data = base64.b64decode(file_data_base64)
            pdf_path = os.path.join("/tmp", f"aip_parse_{uuid.uuid4().hex[:8]}.pdf")
            with open(pdf_path, "wb") as f:
                f.write(file_data)
        except Exception as e:
            self._send(500, {"success": False, "error": str(e)})
            return
        try:
            data = _get_data_from_pdf(pdf_path)
            try:
                os.remove(pdf_path)
            except Exception:
                pass
            self._send(200, {"success": True, "data": data})
        except Exception as e:
            try:
                os.remove(pdf_path)
            except Exception:
                pass
            self._send(500, {"success": False, "error": str(e)})

    def _send(self, status: int, obj: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())
