import os
import sys
import json
from http.server import BaseHTTPRequestHandler

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

from parser_ad2_10 import extract_ad2_10

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Get file data from request body
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "error": "No file data provided"
            }).encode())
            return
        
        # Read request body
        request_data = self.rfile.read(content_length)
        try:
            body = json.loads(request_data.decode('utf-8'))
            file_data_base64 = body.get('fileData')
        except:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "error": "Invalid request body"
            }).encode())
            return
        
        if not file_data_base64:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "error": "No PDF uploaded. Please upload a PDF first."
            }).encode())
            return
        
        # Decode base64 and save to temp file
        import base64
        import uuid
        try:
            file_data = base64.b64decode(file_data_base64)
            temp_dir = '/tmp'
            unique_id = uuid.uuid4().hex[:8]
            pdf_path = os.path.join(temp_dir, f"aip_parse_{unique_id}.pdf")
            
            with open(pdf_path, 'wb') as f:
                f.write(file_data)
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "error": f"Failed to process file: {str(e)}"
            }).encode())
            return
        
        try:
            data = extract_ad2_10(pdf_path)
            # Clean up temp file
            try:
                os.remove(pdf_path)
            except:
                pass
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "data": data}).encode())
        except Exception as e:
            # Clean up temp file on error
            try:
                os.remove(pdf_path)
            except:
                pass
            
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "error": str(e)
            }).encode())
