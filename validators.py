"""
输入验证模块
"""
import re
from typing import Dict, List, Optional, Tuple

class ValidationError(Exception):
    """验证错误异常"""
    pass

class InputValidator:
    """输入验证器"""
    
    @staticmethod
    def validate_base_url(base_url: str) -> Tuple[bool, Optional[str]]:
        """
        验证API基础URL
        
        Args:
            base_url: API基础URL
            
        Returns:
            (是否有效, 错误信息)
        """
        if not base_url or not base_url.strip():
            return False, "API基础URL不能为空"
        
        # 检查URL格式
        try:
            from urllib.parse import urlparse
            import re
            
            parsed = urlparse(base_url.strip())
            
            # 检查scheme
            if parsed.scheme not in ['http', 'https']:
                return False, "URL必须以http://或https://开头"
            
            # 检查netloc
            if not parsed.netloc:
                return False, "URL格式不正确，缺少域名"
            
            # 检查域名格式（支持域名、localhost、IP地址）
            hostname = parsed.hostname
            if hostname:
                # 检查是否为localhost
                if hostname == 'localhost':
                    pass  # localhost是有效的
                # 检查是否为IP地址
                elif re.match(r'^(\d{1,3}\.){3}\d{1,3}$', hostname):
                    pass  # IP地址是有效的
                # 检查是否为域名
                elif '.' not in hostname:
                    return False, "域名格式不正确"
            else:
                return False, "无法解析主机名"
            
            # 更宽松的API路径检查 - 只要包含常见的API相关路径即可
            url_lower = base_url.lower()
            api_patterns = ['/api', '/v1', '/v2', '/v3', '/v4', 'api.', 'openai']
            if not any(pattern in url_lower for pattern in api_patterns):
                return False, "URL应该是API服务地址，例如：https://api.example.com/v3"
            
        except Exception as e:
            return False, f"URL格式验证失败: {str(e)}"
        
        return True, None
    
    @staticmethod
    def validate_api_key(api_key: str) -> Tuple[bool, Optional[str]]:
        """
        验证API密钥
        
        Args:
            api_key: API密钥
            
        Returns:
            (是否有效, 错误信息)
        """
        if not api_key or not api_key.strip():
            return False, "API密钥不能为空"
        
        # 检查长度
        if len(api_key.strip()) < 10:
            return False, "API密钥长度不足"
        
        return True, None
    
    @staticmethod
    def validate_model_endpoint(endpoint: str) -> Tuple[bool, Optional[str]]:
        """
        验证模型端点
        
        Args:
            endpoint: 端点ID
            
        Returns:
            (是否有效, 错误信息)
        """
        if not endpoint or not endpoint.strip():
            return False, "模型端点不能为空"
        
        # 基本格式检查
        endpoint = endpoint.strip()
        if len(endpoint) < 3:
            return False, "模型端点格式不正确"
        
        return True, None
    
    @staticmethod
    def validate_user_content(content: str) -> Tuple[bool, Optional[str]]:
        """
        验证用户输入内容
        
        Args:
            content: 用户输入内容
            
        Returns:
            (是否有效, 错误信息)
        """
        if not content or not content.strip():
            return False, "用户输入不能为空"
        
        # 检查长度限制
        if len(content.strip()) > 10000:
            return False, "用户输入内容过长（最大10000字符）"
        
        return True, None
    
    @staticmethod
    def validate_system_content(content: str) -> Tuple[bool, Optional[str]]:
        """
        验证系统消息内容
        
        Args:
            content: 系统消息内容
            
        Returns:
            (是否有效, 错误信息)
        """
        # 系统消息是可选的，可以为空
        if content and len(content.strip()) > 5000:
            return False, "系统消息内容过长（最大5000字符）"
        
        return True, None
    
    @staticmethod
    def validate_model_id(model_id: str) -> Tuple[bool, Optional[str]]:
        """
        验证模型ID
        
        Args:
            model_id: 模型ID
            
        Returns:
            (是否有效, 错误信息)
        """
        # 模型ID是可选的
        if model_id and len(model_id.strip()) < 2:
            return False, "模型ID格式不正确"
        
        return True, None
    
    @classmethod
    def validate_chat_request(cls, data: Dict) -> List[str]:
        """
        验证聊天请求数据
        
        Args:
            data: 请求数据
            
        Returns:
            错误信息列表
        """
        errors = []
        
        # 验证API密钥
        api_key = data.get('api_key', '').strip()
        is_valid, error = cls.validate_api_key(api_key)
        if not is_valid:
            errors.append(error)
        
        # 验证base_url（可选，如果提供则验证）
        base_url = data.get('base_url', '').strip()
        if base_url:
            is_valid, error = cls.validate_base_url(base_url)
            if not is_valid:
                errors.append(error)
        
        # 验证模型端点
        model_endpoint = data.get('model_endpoint', '').strip()
        is_valid, error = cls.validate_model_endpoint(model_endpoint)
        if not is_valid:
            errors.append(error)
        
        # 检查是否为多轮对话模式
        multi_turn = data.get('multi_turn', False)
        messages = data.get('messages', [])
        
        if multi_turn and messages:
            # 多轮对话模式：验证消息列表
            if not isinstance(messages, list):
                errors.append("消息列表格式不正确")
            else:
                if len(messages) == 0:
                    errors.append("消息列表不能为空")
                elif len(messages) > 50:  # 限制最大消息数量
                    errors.append("消息数量过多（最大50条）")
                else:
                    # 验证每条消息
                    for i, msg in enumerate(messages):
                        if not isinstance(msg, dict):
                            errors.append(f"消息 {i+1} 格式不正确")
                            continue
                        
                        role = msg.get('role', '')
                        content = msg.get('content', '')
                        
                        if role not in ['system', 'user', 'assistant']:
                            errors.append(f"消息 {i+1} 角色无效（必须是 system、user 或 assistant）")
                        
                        # 允许用户消息为空（用于测试系统消息或让模型自由发挥）
                        # 但系统消息和助手消息不应为空
                        if role in ['system', 'assistant'] and (not content or not content.strip()):
                            errors.append(f"消息 {i+1} ({role}) 内容不能为空")
                        elif content and len(content.strip()) > 10000:
                            errors.append(f"消息 {i+1} 内容过长（最大10000字符）")
        else:
            # 单轮对话模式：验证传统字段
            # 允许空用户消息（用于测试系统消息或让模型自由发挥）
            user_content = data.get('user_content', '').strip()
            if user_content and len(user_content) > 10000:
                errors.append("用户输入内容过长（最大10000字符）")
            
            # 验证系统消息（可选）
            system_content = data.get('system_content', '').strip()
            is_valid, error = cls.validate_system_content(system_content)
            if not is_valid:
                errors.append(error)
        
        # 验证模型ID（可选）
        model_id = data.get('model_id', '').strip()
        is_valid, error = cls.validate_model_id(model_id)
        if not is_valid:
            errors.append(error)
        
        return errors
    
    @staticmethod
    def sanitize_api_key(api_key: str) -> str:
        """
        清理API密钥，只进行基本的trim操作，保持特殊字符完整性
        
        Args:
            api_key: 原始API密钥
            
        Returns:
            清理后的API密钥
        """
        if not api_key:
            return ""
        
        # 只进行trim操作，不移除任何字符
        return api_key.strip()
    
    @staticmethod
    def sanitize_url(url: str) -> str:
        """
        清理URL，保留URL中的重要字符
        
        Args:
            url: 原始URL
            
        Returns:
            清理后的URL
        """
        if not url:
            return ""
        
        # 只进行trim操作，保留URL中的所有重要字符
        return url.strip()
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        清理输入文本
        
        Args:
            text: 输入文本
            
        Returns:
            清理后的文本
        """
        if not text:
            return ""
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 移除潜在的恶意字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()[\]{}"\'-]', '', text)
        
        return text