import json
import sys
import os
from pathlib import Path

# Add lib to Python path
ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT / "lib"))

try:
    from pdf_to_elements import pdf_path_to_elements
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def handler(event, context=None):
    """
    Vercel serverless function handler
    """
    # Handle different event formats (Vercel vs local)
    if hasattr(event, 'method'):
        # Local/development format
        method = event.method
        body = event.body if hasattr(event, 'body') else '{}'
    else:
        # Vercel format
        method = event.get('httpMethod', event.get('method', 'GET'))
        body = event.get('body', '{}')
    
    # Handle CORS preflight
    if method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": ""
        }
    
    if method != "POST":
        return {
            "statusCode": 405,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps({"error": "Method Not Allowed"})
        }

    try:
        # Parse request body
        if isinstance(body, bytes):
            body_str = body.decode("utf-8")
        else:
            body_str = body
            
        body_data = json.loads(body_str)
        pdf_url = body_data.get("pdfUrl")
        
        if not pdf_url or not isinstance(pdf_url, str):
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Content-Type": "application/json"
                },
                "body": json.dumps({"error": "pdfUrl نامعتبر یا موجود نیست"})
            }

        # Process PDF
        tables = pdf_path_to_elements(pdf_url)
        
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps({"success": True, "tables": tables})
        }
    
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps({"error": str(e)})
        }