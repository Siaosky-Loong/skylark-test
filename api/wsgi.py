import os
import sys
import time
import json
import uuid
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from services import ModelArkService
    from validators import InputValidator
    from config import VercelConfig
    from logger_utils_vercel import setup_logger
    
    # 创建Vercel配置对象
    config = VercelConfig()
    logger = setup_logger(config)
    
except ImportError as e:
    print(f"Import error: {e}")
    # 如果导入失败，创建简单的替代类
    class ModelArkService:
        def __init__(self, *args, **kwargs):
            pass
        def chat_completion(self, *args, **kwargs):
            return {"choices": [{"message": {"content": "服务暂时不可用"}}]}
    
    class InputValidator:
        @staticmethod
        def validate_chat_request(data):
            return True, None
    
    # 简单的日志设置
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('vercel_api')

# 配置Flask应用，指定模板和静态文件目录
app = Flask(__name__, 
           template_folder=os.path.join(project_root, 'templates'),
           static_folder=os.path.join(project_root, 'static'))
CORS(app)

@app.route('/', methods=['GET'])
def index():
    """渲染聊天界面"""
    return render_template('index.html')

@app.route('/api', methods=['GET'])
def api_status():
    """API状态检查"""
    return jsonify({
        'status': 'success',
        'message': 'WSGI Flask API is working',
        'method': 'GET'
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': time.time()
    })

@app.route('/chat', methods=['POST'])
def chat():
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    try:
        logger.info(f"[{request_id}] 收到聊天请求")
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                'error': '请求体不能为空',
                'status': 'error'
            }), 400
        
        # 验证输入
        is_valid, error_msg = InputValidator.validate_chat_request(data)
        if not is_valid:
            logger.warning(f"[{request_id}] 输入验证失败: {error_msg}")
            return jsonify({
                'error': error_msg,
                'status': 'error'
            }), 400
        
        # 提取参数
        api_key = data.get('api_key')
        base_url = data.get('base_url')
        model_id = data.get('model_id', 'skylark-pro-sc-250615')
        messages = data.get('messages', [])
        
        if not api_key or not base_url:
            return jsonify({
                'error': 'api_key和base_url是必需的',
                'status': 'error'
            }), 400
        
        # 初始化服务
        service = ModelArkService(
            api_key=api_key,
            base_url=base_url,
            model_id=model_id
        )
        
        logger.info(f"[{request_id}] 开始调用API...")
        api_start_time = time.time()
        
        # 调用API
        response = service.chat_completion(
            messages=messages,
            **{k: v for k, v in data.items() if k not in ['api_key', 'base_url', 'model_id', 'messages']}
        )
        
        api_end_time = time.time()
        total_time = api_end_time - start_time
        api_time = api_end_time - api_start_time
        
        logger.info(f"[{request_id}] === 请求处理成功 ===")
        logger.info(f"[{request_id}] 总耗时: {total_time:.2f}秒")
        logger.info(f"[{request_id}] API耗时: {api_time:.2f}秒")
        
        return jsonify({
            'status': 'success',
            'data': response,
            'request_id': request_id,
            'processing_time': {
                'total': round(total_time, 2),
                'api_call': round(api_time, 2)
            }
        })
        
    except Exception as e:
        error_time = time.time() - start_time
        logger.error(f"[{request_id}] 处理请求时发生错误: {str(e)}")
        
        return jsonify({
            'error': f'处理请求时发生错误: {str(e)}',
            'status': 'error',
            'request_id': request_id,
            'processing_time': round(error_time, 2)
        }), 500

@app.route('/test', methods=['POST'])
def test_post():
    try:
        data = request.get_json() or {}
        return jsonify({
            'status': 'success',
            'message': 'POST request received',
            'data': data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Vercel expects an 'app' variable for WSGI applications
if __name__ == '__main__':
    app.run(debug=True)