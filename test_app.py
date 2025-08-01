"""
单元测试
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from validators import InputValidator
from services import ModelArkService

class TestInputValidator(unittest.TestCase):
    """输入验证器测试"""
    
    def test_validate_api_key(self):
        """测试API密钥验证"""
        # 有效的API密钥
        is_valid, error = InputValidator.validate_api_key("valid_api_key_123")
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        
        # 空API密钥
        is_valid, error = InputValidator.validate_api_key("")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        
        # 过短的API密钥
        is_valid, error = InputValidator.validate_api_key("short")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_api_key_sanitization(self):
        """测试API密钥清理"""
        # API密钥应该保持特殊字符完整性
        api_key = "sk-1234567890abcdef!@#$%^&*()_+-=[]{}|;':\",./<>?"
        sanitized = InputValidator.sanitize_api_key(api_key)
        self.assertEqual(sanitized, api_key)  # 应该保持不变
        
        # 只应该移除首尾空格
        api_key_with_spaces = "  sk-1234567890abcdef  "
        sanitized = InputValidator.sanitize_api_key(api_key_with_spaces)
        self.assertEqual(sanitized, "sk-1234567890abcdef")
        
        # 空字符串处理
        self.assertEqual(InputValidator.sanitize_api_key(""), "")
        self.assertEqual(InputValidator.sanitize_api_key("   "), "")
    
    def test_validate_user_content(self):
        """测试用户内容验证"""
        # 有效内容
        is_valid, error = InputValidator.validate_user_content("Hello, world!")
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        
        # 空内容
        is_valid, error = InputValidator.validate_user_content("")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        
        # 过长内容
        long_content = "x" * 10001
        is_valid, error = InputValidator.validate_user_content(long_content)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_sanitize_input(self):
        """测试输入清理"""
        # 测试空白字符清理
        result = InputValidator.sanitize_input("  hello   world  ")
        self.assertEqual(result, "hello world")
        
        # 测试空输入
        result = InputValidator.sanitize_input("")
        self.assertEqual(result, "")
        
        # 测试None输入
        result = InputValidator.sanitize_input(None)
        self.assertEqual(result, "")

class TestModelArkService(unittest.TestCase):
    """ModelArk服务测试"""
    
    @patch('services.OpenAI')
    def test_service_initialization(self, mock_openai):
        """测试服务初始化"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        service = ModelArkService("test_api_key")
        self.assertIsNotNone(service.client)
        mock_openai.assert_called_once()
    
    def test_build_messages(self):
        """测试消息构建"""
        with patch('services.OpenAI'):
            service = ModelArkService("test_api_key")
            
            # 只有用户消息
            messages = service.build_messages("Hello")
            self.assertEqual(len(messages), 1)
            self.assertEqual(messages[0]["role"], "user")
            self.assertEqual(messages[0]["content"], "Hello")
            
            # 包含系统消息
            messages = service.build_messages("Hello", "You are a helpful assistant")
            self.assertEqual(len(messages), 2)
            self.assertEqual(messages[0]["role"], "system")
            self.assertEqual(messages[1]["role"], "user")

if __name__ == '__main__':
    unittest.main()