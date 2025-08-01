"""
Vercel部署的简化Flask应用
"""
import os
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# 设置Vercel环境变量
os.environ['FLASK_ENV'] = 'vercel'

try:
    import sys
    sys.path.append('/var/task')
    
    from config import get_config
    from services import ModelArkService
    from validators import InputValidator
    from logger_utils_vercel import generate_request_id
except ImportError as e:
    print(f"导入错误: {e}")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """处理GET请求"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'status': 'healthy',
                'version': '1.0.0'
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            # 返回简单的HTML页面
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Skylark Test API</title>
            </head>
            <body>
                <h1>Skylark Test API</h1>
                <p>API is running on Vercel</p>
                <p>Use POST /chat for chat requests</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
    
    def do_POST(self):
        """处理POST请求"""
        try:
            if self.path == '/chat':
                self.handle_chat()
            else:
                self.send_error(404, "Not Found")
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {
                'success': False,
                'error': f'服务器错误: {str(e)}'
            }
            self.wfile.write(json.dumps(error_response).encode())
    
    def handle_chat(self):
        """处理聊天请求"""
        try:
            # 读取请求数据
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            request_id = generate_request_id()
            
            # 获取配置
            config = get_config()
            
            # 验证输入数据
            validation_errors = InputValidator.validate_chat_request(data)
            if validation_errors:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_response = {
                    'success': False,
                    'error': '; '.join(validation_errors),
                    'request_id': request_id
                }
                self.wfile.write(json.dumps(error_response).encode())
                return
            
            # 获取API参数
            api_key = data.get('api_key') or config.ARK_API_KEY
            base_url = data.get('base_url') or config.ARK_BASE_URL
            model_endpoint = data.get('model_endpoint', '')
            model_id = data.get('model_id', '')
            system_content = data.get('system_content', '')
            user_content = data.get('user_content', '')
            
            if not api_key:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_response = {
                    'success': False,
                    'error': 'API密钥未提供',
                    'request_id': request_id
                }
                self.wfile.write(json.dumps(error_response).encode())
                return
            
            # 确定使用的模型参数
            model_param = model_id if model_id else model_endpoint
            
            # 创建API服务实例
            service = ModelArkService(api_key, base_url, request_id)
            
            # 构建消息
            messages = service.build_messages(user_content, system_content)
            
            # 调用API
            result = service.create_chat_completion(
                model=model_param,
                messages=messages
            )
            
            # 返回响应
            if result['success']:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response_data = {
                    'success': True,
                    'response': result['content'],
                    'model': result['model'],
                    'usage': result['usage'],
                    'finish_reason': result['finish_reason'],
                    'request_id': request_id
                }
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                result['request_id'] = request_id
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {
                'success': False,
                'error': f'请求处理失败: {str(e)}',
                'request_id': generate_request_id()
            }
            self.wfile.write(json.dumps(error_response).encode())