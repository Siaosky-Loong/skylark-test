import os
import time
import asyncio
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
from io import BytesIO

# 设置Vercel环境
os.environ['FLASK_ENV'] = 'vercel'

from config import get_config
from services import ModelArkService
from validators import InputValidator
from logger_utils_vercel import generate_request_id

# 获取配置
config = get_config()

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(config)
CORS(app)

@app.route('/')
def index():
    """渲染主页面"""
    return render_template('index.html')

@app.route('/health')
def health():
    """健康检查端点，用于心跳机制"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/chat', methods=['POST'])
def chat():
    """处理聊天请求"""
    request_id = generate_request_id()
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据不能为空',
                'request_id': request_id
            }), 400
        
        # 验证输入数据
        validation_errors = InputValidator.validate_chat_request(data)
        if validation_errors:
            return jsonify({
                'success': False,
                'error': '; '.join(validation_errors),
                'request_id': request_id
            }), 400
        
        # 获取并处理输入数据
        api_key = InputValidator.sanitize_api_key(data.get('api_key', ''))
        base_url = InputValidator.sanitize_url(data.get('base_url', ''))
        model_endpoint = InputValidator.sanitize_input(data.get('model_endpoint', ''))
        model_id = InputValidator.sanitize_input(data.get('model_id', ''))
        
        # 检查是否为多轮对话模式
        multi_turn = data.get('multi_turn', False)
        messages = data.get('messages', [])
        
        # 处理logit_bias参数
        logit_bias = data.get('logit_bias')
        
        # 如果前端没有提供API密钥，尝试从环境变量获取
        if not api_key:
            api_key = config.ARK_API_KEY
            if not api_key:
                return jsonify({
                    'success': False,
                    'error': 'API密钥未提供。请在页面中输入API密钥或在环境变量中设置ARK_API_KEY。',
                    'request_id': request_id
                }), 400
        
        # 如果前端没有提供base_url，使用配置中的默认值
        if not base_url:
            base_url = config.ARK_BASE_URL
        
        # 验证base_url格式
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(base_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("无效的URL格式")
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'请求地址格式无效: {str(e)}。请输入有效的URL，例如：https://ark.cn-beijing.volces.com/api/v3',
                'request_id': request_id
            }), 400
        
        # 确定使用的模型参数
        model_param = model_id if model_id else model_endpoint
        
        # 创建API服务实例
        try:
            service = ModelArkService(api_key, base_url, request_id)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'服务初始化失败: {str(e)}',
                'request_id': request_id
            }), 500
        
        # 构建消息
        if multi_turn and messages:
            # 多轮对话模式：直接使用前端传来的消息列表
            final_messages = messages
        else:
            # 单轮对话模式：使用传统方式构建消息
            system_content = InputValidator.sanitize_input(data.get('system_content', ''))
            user_content = InputValidator.sanitize_input(data.get('user_content', ''))
            final_messages = service.build_messages(user_content, system_content)
        
        # 调用API
        result = service.create_chat_completion(
            model=model_param,
            messages=final_messages,
            logit_bias=logit_bias
        )
        
        # 计算总耗时
        total_duration = time.time() - start_time
        
        if result['success']:
            # 构建返回给前端的响应数据
            response_data = {
                'success': True,
                'response': result['content'],  # 将content映射为response字段
                'model': result['model'],
                'usage': result['usage'],
                'finish_reason': result['finish_reason'],
                'request_id': request_id,
                'total_duration': total_duration,
                'api_duration': result.get('duration', 0)
            }
            
            return jsonify(response_data)
        else:
            # 添加请求追踪信息
            result['request_id'] = request_id
            result['total_duration'] = total_duration
            
            return jsonify(result), 500
        
    except Exception as e:
        total_duration = time.time() - start_time
        
        # 不在日志中显示API密钥
        error_msg = str(e)
        if 'api_key' in error_msg.lower():
            error_msg = "API认证失败，请检查API密钥是否正确"
        
        return jsonify({
            'success': False,
            'error': f'请求失败: {error_msg}',
            'request_id': request_id,
            'total_duration': total_duration
        }), 500

@app.route('/batch_chat', methods=['POST'])
def batch_chat():
    """处理批量聊天请求 - 返回内存中的Excel文件"""
    request_id = generate_request_id()
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据不能为空',
                'request_id': request_id
            }), 400
        
        # 获取批量请求参数
        batch_count = data.get('batch_count', 1)
        batch_concurrency = data.get('batch_concurrency', 1)
        
        # 验证批量参数
        if not isinstance(batch_count, int) or batch_count < 1:
            return jsonify({
                'success': False,
                'error': '请求次数必须是大于等于1的整数',
                'request_id': request_id
            }), 400
        
        if not isinstance(batch_concurrency, int) or batch_concurrency < 1:
            return jsonify({
                'success': False,
                'error': '并发数必须是大于等于1的整数',
                'request_id': request_id
            }), 400
        
        # 验证基本输入数据
        validation_errors = InputValidator.validate_chat_request(data)
        if validation_errors:
            return jsonify({
                'success': False,
                'error': '; '.join(validation_errors),
                'request_id': request_id
            }), 400
        
        # 获取并处理输入数据
        api_key = InputValidator.sanitize_api_key(data.get('api_key', ''))
        base_url = InputValidator.sanitize_url(data.get('base_url', ''))
        system_content = InputValidator.sanitize_input(data.get('system_content', ''))
        user_content = InputValidator.sanitize_input(data.get('user_content', ''))
        model_endpoint = InputValidator.sanitize_input(data.get('model_endpoint', ''))
        model_id = InputValidator.sanitize_input(data.get('model_id', ''))
        logit_bias = data.get('logit_bias')
        
        # 如果前端没有提供API密钥，尝试从环境变量获取
        if not api_key:
            api_key = config.ARK_API_KEY
            if not api_key:
                return jsonify({
                    'success': False,
                    'error': 'API密钥未提供',
                    'request_id': request_id
                }), 400
        
        # 如果前端没有提供base_url，使用配置中的默认值
        if not base_url:
            base_url = config.ARK_BASE_URL
        
        # 确定使用的模型参数
        model_param = model_id if model_id else model_endpoint
        
        # 执行批量请求
        results = process_batch_requests(
            api_key, base_url, model_param, system_content, user_content, 
            logit_bias, batch_count, batch_concurrency, request_id
        )
        
        # 计算总耗时
        total_duration = time.time() - start_time
        
        # 生成Excel文件内容（Base64编码）
        excel_data = generate_excel_data(results, user_content, total_duration)
        
        return jsonify({
            'success': True,
            'excel_data': excel_data,
            'filename': f'batch_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            'total_duration': total_duration,
            'request_id': request_id
        })
        
    except Exception as e:
        total_duration = time.time() - start_time
        
        return jsonify({
            'success': False,
            'error': f'批量请求失败: {str(e)}',
            'request_id': request_id,
            'total_duration': total_duration
        }), 500

def process_batch_requests(api_key, base_url, model_param, system_content, user_content, 
                          logit_bias, batch_count, batch_concurrency, request_id):
    """处理批量请求"""
    import concurrent.futures
    import threading
    
    results = []
    completed_count = 0
    lock = threading.Lock()
    
    def single_request(index):
        """单个请求处理函数"""
        nonlocal completed_count
        
        single_request_id = f"{request_id}-{index+1}"
        start_time = time.time()
        
        try:
            # 创建API服务实例
            service = ModelArkService(api_key, base_url, single_request_id)
            
            # 构建消息
            messages = service.build_messages(user_content, system_content)
            
            # 调用API
            result = service.create_chat_completion(
                model=model_param,
                messages=messages,
                logit_bias=logit_bias
            )
            
            duration = time.time() - start_time
            
            with lock:
                completed_count += 1
            
            return {
                'index': index + 1,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'success': result['success'],
                'content': result.get('content', ''),
                'error': result.get('error', ''),
                'duration': duration * 1000,  # 转换为毫秒
                'usage': result.get('usage', {}),
                'model': result.get('model', model_param)
            }
            
        except Exception as e:
            duration = time.time() - start_time
            
            with lock:
                completed_count += 1
            
            return {
                'index': index + 1,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'success': False,
                'content': '',
                'error': str(e),
                'duration': duration * 1000,
                'usage': {},
                'model': model_param
            }
    
    # 使用线程池执行批量请求
    with concurrent.futures.ThreadPoolExecutor(max_workers=batch_concurrency) as executor:
        futures = [executor.submit(single_request, i) for i in range(batch_count)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    # 按索引排序结果
    results.sort(key=lambda x: x['index'])
    
    return results

def generate_excel_data(results, user_input, total_duration):
    """生成Excel文件数据并返回Base64编码"""
    import base64
    
    # 准备数据
    data = []
    for result in results:
        data.append({
            '序号': result['index'],
            '时间戳': result['timestamp'],
            '用户输入内容': user_input,
            '模型响应内容': result['content'] if result['success'] else f"错误: {result['error']}",
            '响应耗时(毫秒)': round(result['duration'], 2),
            '请求状态': '成功' if result['success'] else '失败',
            '模型名称': result['model'],
            '输入Token数': result['usage'].get('prompt_tokens', 0) if result['success'] else 0,
            '输出Token数': result['usage'].get('completion_tokens', 0) if result['success'] else 0,
            '总Token数': result['usage'].get('total_tokens', 0) if result['success'] else 0
        })
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 创建Excel文件
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        # 写入主数据
        df.to_excel(writer, sheet_name='批量请求结果', index=False)
        
        # 添加统计信息
        summary_data = {
            '统计项': ['总请求数', '成功数', '失败数', '成功率', '总耗时(秒)', '平均响应时间(毫秒)'],
            '数值': [
                len(results),
                len([r for r in results if r['success']]),
                len([r for r in results if not r['success']]),
                f"{len([r for r in results if r['success']]) / len(results) * 100:.1f}%",
                round(total_duration, 2),
                round(sum([r['duration'] for r in results]) / len(results), 2)
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='统计信息', index=False)
    
    excel_buffer.seek(0)
    excel_data = base64.b64encode(excel_buffer.getvalue()).decode('utf-8')
    return excel_data

@app.route('/health')
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': time.time()
    })

# Vercel需要的handler
def handler(request):
    return app(request.environ, lambda status, headers: None)

if __name__ == '__main__':
    app.run(
        debug=config.DEBUG,
        host=config.HOST,
        port=config.PORT
    )