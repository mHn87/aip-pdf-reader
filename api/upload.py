import os
import sys
import tempfile
import uuid
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs
import cgi

# Add parent directory to path for importing parsers
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Parse multipart form data
            content_type = self.headers.get('Content-Type', '')
            if not content_type.startswith('multipart/form-data'):
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Invalid content type"}).encode())
                return
            
            # Parse form data
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            
            # Get file from form
            if 'file' not in form:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "No file provided"}).encode())
                return
            
            file_item = form['file']
            filename = file_item.filename or 'uploaded_file.pdf'
            
            if not filename.lower().endswith('.pdf'):
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Only PDF files are allowed"}).encode())
                return
            
            # Read file data
            file_data = file_item.file.read()
            
            # Create temp file
            temp_dir = '/tmp'  # Vercel uses /tmp
            safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
            if not safe_filename:
                safe_filename = "uploaded_file"
            
            unique_id = uuid.uuid4().hex[:8]
            temp_path = os.path.join(temp_dir, f"aip_upload_{unique_id}_{safe_filename}")
            
            # Write file
            with open(temp_path, 'wb') as f:
                f.write(file_data)
            
            # Generate a unique file ID
            file_id = unique_id
            
            # Store file path mapping in a simple JSON file in /tmp
            # Note: This is a workaround. For production, use Vercel KV or a database
            mapping_file = '/tmp/aip_file_mappings.json'
            mappings = {}
            if os.path.exists(mapping_file):
                try:
                    with open(mapping_file, 'r') as f:
                        mappings = json.load(f)
                except:
                    mappings = {}
            
            mappings[file_id] = {
                'path': temp_path,
                'filename': filename,
                'timestamp': os.path.getmtime(temp_path) if os.path.exists(temp_path) else 0
            }
            
            # Clean up old mappings (older than 1 hour)
            import time
            current_time = time.time()
            mappings = {k: v for k, v in mappings.items() 
                       if current_time - v.get('timestamp', 0) < 3600}
            
            with open(mapping_file, 'w') as f:
                json.dump(mappings, f)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "filename": filename,
                "fileId": file_id,
                "message": "PDF uploaded successfully",
                "size": len(file_data)
            }).encode())
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "error": str(e),
                "detail": error_detail
            }).encode())
