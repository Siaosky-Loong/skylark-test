import os
import logging
import logging.handlers
import time
import asyncio
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
from io import BytesIO

from config import get_config
from services import ModelArkService
from validators import InputValidator
from logger_utils import APILogger, generate_request_id

# 获取配置
config = get_config()

# 创建API日志记录器
api_logger = APILogger(config)

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(config)
CORS(app)

# 获取应用日志记录器
logger = api_logger.app_logger

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
        logger.info(f"[{request_id}] === 新的聊天请求开始 ===")
        data = request.get_json()
        
        if not data:
            logger.warning(f"[{request_id}] 请求数据为空")
            return jsonify({
                'success': False,
                'error': '请求数据不能为空',
                'request_id': request_id
            }), 400
        
        # 记录原始请求数据（脱敏）
        logger.info(f"[{request_id}] 请求数据字段: {list(data.keys())}")
        
        # 验证输入数据
        validation_errors = InputValidator.validate_chat_request(data)
        if validation_errors:
            logger.warning(f"[{request_id}] 输入验证失败: {validation_errors}")
            return jsonify({
                'success': False,
                'error': '; '.join(validation_errors),
                'request_id': request_id
            }), 400
        
        # 获取并处理输入数据
        # API密钥使用专门的处理函数，保持原始完整性
        api_key = InputValidator.sanitize_api_key(data.get('api_key', ''))
        # 其他输入进行安全清理
        base_url = InputValidator.sanitize_url(data.get('base_url', ''))
        model_endpoint = InputValidator.sanitize_input(data.get('model_endpoint', ''))
        model_id = InputValidator.sanitize_input(data.get('model_id', ''))
        
        # 检查是否为多轮对话模式
        multi_turn = data.get('multi_turn', False)
        messages = data.get('messages', [])
        
        # 处理消息数据
        if multi_turn and messages:
            # 多轮对话模式：使用前端传来的完整消息列表
            logger.info(f"[{request_id}] 多轮对话模式，消息数量: {len(messages)}")
            for i, msg in enumerate(messages):
                role = msg.get('role', 'unknown')
                content_length = len(msg.get('content', ''))
                logger.info(f"[{request_id}] 消息 {i+1}: {role} ({content_length} 字符)")
        else:
            # 单轮对话模式：使用传统的system_content和user_content
            system_content = InputValidator.sanitize_input(data.get('system_content', ''))
            user_content = InputValidator.sanitize_input(data.get('user_content', ''))
            logger.info(f"[{request_id}] 单轮对话模式")
            logger.info(f"[{request_id}] 用户输入长度: {len(user_content)} 字符")
            logger.info(f"[{request_id}] 系统消息长度: {len(system_content)} 字符")
        
        # 处理logit_bias参数
        logit_bias = data.get('logit_bias')
        if logit_bias is not None:
            logger.info(f"[{request_id}] 收到logit_bias参数: {logit_bias}")
        else:
            logger.info(f"[{request_id}] 未提供logit_bias参数，将使用默认配置")
        # 如果前端没有提供API密钥，尝试从环境变量获取
        if not api_key:
            api_key = config.ARK_API_KEY
            if not api_key:
                logger.warning(f"[{request_id}] API密钥未提供")
                return jsonify({
                    'success': False,
                    'error': 'API密钥未提供。请在页面中输入API密钥或在.env文件中设置ARK_API_KEY环境变量。',
                    'request_id': request_id
                }), 400
        
        # 如果前端没有提供base_url，使用配置中的默认值
        if not base_url:
            base_url = config.ARK_BASE_URL
            logger.info(f"[{request_id}] 使用默认base_url: {base_url}")
        else:
            logger.info(f"[{request_id}] 使用用户提供的base_url: {base_url}")
        
        # 验证base_url格式
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(base_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("无效的URL格式")
        except Exception as e:
            logger.warning(f"[{request_id}] base_url格式验证失败: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'请求地址格式无效: {str(e)}。请输入有效的URL，例如：https://ark.cn-beijing.volces.com/api/v3',
                'request_id': request_id
            }), 400
        
        # 确定使用的模型参数
        model_param = model_id if model_id else model_endpoint
        logger.info(f"[{request_id}] 使用模型参数: {model_param}")
        
        # 记录API密钥信息（开发环境显示完整密钥，生产环境脱敏）
        if config.DEBUG:
            logger.info(f"[{request_id}] API密钥: {api_key} (长度: {len(api_key)})")
        else:
            masked_api_key = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else '*' * 8
            logger.info(f"[{request_id}] API密钥: {masked_api_key} (长度: {len(api_key)})")
        
        # 创建API服务实例
        try:
            service = ModelArkService(api_key, base_url, request_id)
            logger.info(f"[{request_id}] ModelArk服务初始化成功")
        except Exception as e:
            logger.error(f"[{request_id}] 服务初始化失败: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'服务初始化失败: {str(e)}',
                'request_id': request_id
            }), 500
        
        # 构建消息
        if multi_turn and messages:
            # 多轮对话模式：直接使用前端传来的消息列表
            final_messages = messages
            logger.info(f"[{request_id}] 使用多轮对话消息列表，共 {len(final_messages)} 条消息")
        else:
            # 单轮对话模式：使用传统方式构建消息
            final_messages = service.build_messages(user_content, system_content)
            logger.info(f"[{request_id}] 使用单轮对话模式构建消息")
        
        # 调用API
        logger.info(f"[{request_id}] 开始调用API...")
        result = service.create_chat_completion(
            model=model_param,
            messages=final_messages,
            logit_bias=logit_bias
        )
        
        # 计算总耗时
        total_duration = time.time() - start_time
        
        if result['success']:
            logger.info(f"[{request_id}] === 请求处理成功 ===")
            logger.info(f"[{request_id}] 总耗时: {total_duration:.2f}秒")
            logger.info(f"[{request_id}] API耗时: {result.get('duration', 0):.2f}秒")
            
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
            logger.error(f"[{request_id}] === 请求处理失败 ===")
            logger.error(f"[{request_id}] 总耗时: {total_duration:.2f}秒")
            logger.error(f"[{request_id}] 错误: {result['error']}")
            
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
        
        logger.error(f"[{request_id}] === 请求处理异常 ===")
        logger.error(f"[{request_id}] 总耗时: {total_duration:.2f}秒")
        logger.error(f"[{request_id}] 异常类型: {type(e).__name__}")
        logger.error(f"[{request_id}] 异常消息: {error_msg}")
        
        return jsonify({
            'success': False,
            'error': f'请求失败: {error_msg}',
            'request_id': request_id,
            'total_duration': total_duration
        }), 500

@app.route('/batch_chat', methods=['POST'])
def batch_chat():
    """处理批量聊天请求"""
    request_id = generate_request_id()
    start_time = time.time()
    
    try:
        logger.info(f"[{request_id}] === 新的批量聊天请求开始 ===")
        data = request.get_json()
        
        if not data:
            logger.warning(f"[{request_id}] 批量请求数据为空")
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
        
        logger.info(f"[{request_id}] 批量请求参数: 次数={batch_count}, 并发={batch_concurrency}")
        
        # 验证基本输入数据（复用单次请求的验证逻辑）
        validation_errors = InputValidator.validate_chat_request(data)
        if validation_errors:
            logger.warning(f"[{request_id}] 批量请求输入验证失败: {validation_errors}")
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
        
        # 生成Excel文件
        excel_file = generate_excel_file(results, user_content, total_duration)
        
        logger.info(f"[{request_id}] === 批量请求处理完成 ===")
        logger.info(f"[{request_id}] 总耗时: {total_duration:.2f}秒")
        logger.info(f"[{request_id}] 成功: {len([r for r in results if r['success']])}/{len(results)}")
        
        # 直接返回Excel文件
        return send_file(
            excel_file,
            as_attachment=True,
            download_name=f'batch_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        total_duration = time.time() - start_time
        logger.error(f"[{request_id}] === 批量请求处理异常 ===")
        logger.error(f"[{request_id}] 总耗时: {total_duration:.2f}秒")
        logger.error(f"[{request_id}] 异常: {str(e)}")
        
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
                logger.info(f"[{single_request_id}] 请求完成 ({completed_count}/{batch_count})")
            
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
                logger.error(f"[{single_request_id}] 请求失败 ({completed_count}/{batch_count}): {str(e)}")
            
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

def generate_excel_file(results, user_input, total_duration):
    """生成Excel文件"""
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
    return excel_buffer

@app.route('/health')
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': time.time()
    })

@app.route('/logs')
def view_logs():
    """查看日志文件内容"""
    try:
        # 获取参数
        log_type = request.args.get('type', 'all')  # all, app, api
        lines_count = int(request.args.get('lines', 500))
        
        # 限制最大行数
        lines_count = min(lines_count, 5000)
        
        logs = []
        total_lines = 0
        
        if log_type in ['all', 'app']:
            # 读取应用日志
            app_log_file = config.LOG_FILE
            if app_log_file and os.path.exists(app_log_file):
                with open(app_log_file, 'r', encoding='utf-8') as f:
                    app_lines = f.readlines()
                    total_lines += len(app_lines)
                    # 添加标识符以区分日志来源
                    app_logs = [f"[APP] {line.rstrip()}" for line in app_lines[-lines_count:]]
                    logs.extend(app_logs)
        
        if log_type in ['all', 'api']:
            # 读取API调用日志
            api_log_file = 'logs/api_calls.log'
            if api_log_file and os.path.exists(api_log_file):
                with open(api_log_file, 'r', encoding='utf-8') as f:
                    api_lines = f.readlines()
                    total_lines += len(api_lines)
                    # 添加标识符以区分日志来源
                    api_logs = [f"[API] {line.rstrip()}" for line in api_lines[-lines_count:]]
                    logs.extend(api_logs)
        
        # 如果是all类型，按时间戳排序（简单排序）
        if log_type == 'all' and logs:
            # 尝试按时间戳排序，如果失败则保持原顺序
            try:
                logs.sort(key=lambda x: x.split(' ')[1:3] if len(x.split(' ')) >= 3 else ['', ''])
            except:
                pass
        
        # 限制返回的行数
        if len(logs) > lines_count:
            logs = logs[-lines_count:]
        
        return jsonify({
            'success': True,
            'logs': logs,
            'total_lines': total_lines,
            'displayed_lines': len(logs),
            'log_type': log_type
        })
        
    except Exception as e:
        logger.error(f"读取日志文件失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'logs': [],
            'total_lines': 0
        })

@app.route('/logs/view')
def logs_page():
    """日志查看页面"""
    return render_template('logs.html')

if __name__ == '__main__':
    logger.info(f"启动应用，配置: {config.__class__.__name__}")
    logger.info(f"日志文件: {config.LOG_FILE}")
    logger.info(f"API基础URL: {config.ARK_BASE_URL}")
    app.run(
        debug=config.DEBUG,
        host=config.HOST,
        port=config.PORT
    )