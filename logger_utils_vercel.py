"""
日志工具模块 - Vercel版本
提供简化的日志记录功能，适用于Serverless环境
"""
import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

class APILogger:
    """API调用日志记录器 - Vercel版本"""
    
    def __init__(self, config):
        self.config = config
        self.setup_loggers()
    
    def setup_loggers(self):
        """设置日志记录器 - 仅控制台输出"""
        # 主应用日志记录器
        self.app_logger = logging.getLogger('app')
        self.app_logger.setLevel(getattr(logging, self.config.LOG_LEVEL))
        
        # API调用日志记录器
        self.api_logger = logging.getLogger('api_calls')
        self.api_logger.setLevel(logging.DEBUG)
        
        # 清除现有的处理器
        self.app_logger.handlers.clear()
        self.api_logger.handlers.clear()
        
        # 仅使用控制台处理器（Vercel环境）
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(self.config.LOG_FORMAT))
        
        # 添加处理器
        self.app_logger.addHandler(console_handler)
        self.api_logger.addHandler(console_handler)
    
    def mask_sensitive_data(self, data: str, mask_char: str = '*') -> str:
        """脱敏敏感数据"""
        if not data or len(data) < 8:
            return mask_char * 8
        
        # 在开发环境中不脱敏，便于调试
        if self.config.DEBUG:
            return data
        
        # 生产环境中脱敏：显示前4位和后4位，中间用*替代
        return data[:4] + mask_char * (len(data) - 8) + data[-4:]
    
    def log_request_start(self, request_id: str, endpoint: str, user_content: str, 
                         api_key: str, model: str):
        """记录请求开始"""
        masked_api_key = self.mask_sensitive_data(api_key)
        
        self.app_logger.info(f"[{request_id}] 开始处理聊天请求")
        self.app_logger.info(f"[{request_id}] 模型: {model}")
        self.app_logger.info(f"[{request_id}] API密钥: {masked_api_key}")
        self.app_logger.info(f"[{request_id}] 用户输入长度: {len(user_content)} 字符")
        
        # API调用详细日志
        self.api_logger.info(f"[{request_id}] === API请求开始 ===")
        self.api_logger.info(f"[{request_id}] 端点: {endpoint}")
        self.api_logger.info(f"[{request_id}] 模型: {model}")
        self.api_logger.info(f"[{request_id}] API密钥: {masked_api_key}")
        self.api_logger.info(f"[{request_id}] 用户输入: {user_content[:200]}{'...' if len(user_content) > 200 else ''}")
    
    def log_api_request(self, request_id: str, request_data: Dict[str, Any]):
        """记录API请求详情"""
        # 脱敏处理
        safe_request = request_data.copy()
        
        self.api_logger.info(f"[{request_id}] API请求参数:")
        self.api_logger.info(f"[{request_id}] {json.dumps(safe_request, ensure_ascii=False, indent=2)}")
    
    def log_api_response(self, request_id: str, response_data: Dict[str, Any], 
                        success: bool = True):
        """记录API响应"""
        status = "成功" if success else "失败"
        self.api_logger.info(f"[{request_id}] API响应 ({status}):")
        self.api_logger.info(f"[{request_id}] {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        
        if success and 'usage' in response_data:
            usage = response_data['usage']
            self.app_logger.info(f"[{request_id}] Token使用情况: "
                               f"输入={usage.get('prompt_tokens', 0)}, "
                               f"输出={usage.get('completion_tokens', 0)}, "
                               f"总计={usage.get('total_tokens', 0)}")
    
    def log_error(self, request_id: str, error: Exception, context: str = ""):
        """记录错误"""
        error_msg = str(error)
        self.app_logger.error(f"[{request_id}] 错误 ({context}): {error_msg}")
        self.api_logger.error(f"[{request_id}] === 错误详情 ===")
        self.api_logger.error(f"[{request_id}] 上下文: {context}")
        self.api_logger.error(f"[{request_id}] 错误类型: {type(error).__name__}")
        self.api_logger.error(f"[{request_id}] 错误消息: {error_msg}")
    
    def log_request_end(self, request_id: str, success: bool, duration: float):
        """记录请求结束"""
        status = "成功" if success else "失败"
        self.app_logger.info(f"[{request_id}] 请求处理完成 ({status}), 耗时: {duration:.2f}秒")
        self.api_logger.info(f"[{request_id}] === API请求结束 ({status}) ===")

def generate_request_id() -> str:
    """生成请求ID"""
    from uuid import uuid4
    return str(uuid4())[:8]