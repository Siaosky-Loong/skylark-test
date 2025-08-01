from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            'status': 'success',
            'message': 'Vercel Python API is working',
            'path': self.path,
            'method': 'GET'
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))
        return

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
            else:
                data = {}
            
            response = {
                'status': 'success',
                'message': 'POST request received',
                'path': self.path,
                'method': 'POST',
                'data': data
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            error_response = {
                'status': 'error',
                'message': f'Error: {str(e)}'
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
        return