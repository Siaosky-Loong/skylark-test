"""
最简单的Vercel测试API
"""
import json
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """处理GET请求"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            'status': 'success',
            'message': 'Simple Vercel API is working',
            'path': self.path
        }
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        """处理POST请求"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            # 读取请求数据
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
            else:
                data = {}
            
            response = {
                'status': 'success',
                'message': 'POST request received',
                'data': data,
                'path': self.path
            }
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            error_response = {
                'status': 'error',
                'message': f'Error processing request: {str(e)}'
            }
            self.wfile.write(json.dumps(error_response).encode())