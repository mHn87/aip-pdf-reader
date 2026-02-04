import os
import sys
import json
from http.server import BaseHTTPRequestHandler

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

from parser_ad2_12 import extract_ad2_12

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Get file ID from query parameter
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        file_id = query_params.get('fileId', [None])[0]
        
        # Load file mappings
        mapping_file = '/tmp/aip_file_mappings.json'
        pdf_path = None
        
        if file_id and os.path.exists(mapping_file):
            try:
                with open(mapping_file, 'r') as f:
                    mappings = json.load(f)
                    if file_id in mappings:
                        pdf_path = mappings[file_id].get('path')
            except:
                pass
        
        # Fallback: try to find any recent file in /tmp
        if not pdf_path or not os.path.exists(pdf_path):
            # Try to find the most recent aip_upload_* file
            temp_dir = '/tmp'
            try:
                import glob
                import time
                pdf_files = glob.glob(os.path.join(temp_dir, 'aip_upload_*.pdf'))
                if pdf_files:
                    # Get the most recent file
                    pdf_path = max(pdf_files, key=os.path.getmtime)
                    # Check if it's recent (within last hour)
                    if time.time() - os.path.getmtime(pdf_path) > 3600:
                        pdf_path = None
            except:
                pass
        
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
            data = extract_ad2_12(pdf_path)
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
