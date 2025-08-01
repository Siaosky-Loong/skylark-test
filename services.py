"""API服务层
负责与BytePlus ModelArk API的交互"""
import logging
import time
import json
from typing import Dict, List, Optional, Any
from openai import OpenAI
from config import get_config

class ModelArkService:
    """BytePlus ModelArk API服务类"""
    
    def __init__(self, api_key: str, base_url: str = None, request_id: str = None):
        """
        初始化服务
        
        Args:
            api_key: API密钥
            base_url: API基础URL，如果不提供则使用配置中的默认值
            request_id: 请求ID，用于日志追踪
        """
        self.config = get_config()
        self.api_key = api_key
        self.base_url = base_url or self.config.ARK_BASE_URL
        self.request_id = request_id or "unknown"
        self.logger = logging.getLogger('api_calls')
        
        # 初始化OpenAI客户端
        try:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=api_key
            )
            self.logger.info(f"[{self.request_id}] OpenAI客户端初始化成功")
            self.logger.info(f"[{self.request_id}] 基础URL: {self.base_url}")
        except Exception as e:
            self.logger.error(f"[{self.request_id}] OpenAI客户端初始化失败: {str(e)}")
            raise
    
    def create_chat_completion(self, model: str, messages: List[Dict[str, str]], logit_bias: Dict = None) -> Dict[str, Any]:
        """
        创建聊天完成
        
        Args:
            model: 模型名称或端点
            messages: 消息列表
            
        Returns:
            包含响应结果的字典
        """
        start_time = time.time()
        
        try:
            # 构建请求参数
            request_params = {
                "model": model,
                "messages": messages,
                "temperature": self.config.DEFAULT_TEMPERATURE,
               "max_tokens": self.config.DEFAULT_MAX_TOKENS,
                "top_p": self.config.DEFAULT_TOP_P,
              #   "frequency_penalty": self.config.DEFAULT_FREQUENCY_PENALTY,
                # "presence_penalty": self.config.DEFAULT_PRESENCE_PENALTY,
            }
            
            # 如果提供了logit_bias参数，使用它；否则使用配置中的默认值
            if logit_bias is not None:
                request_params["logit_bias"] = logit_bias
                self.logger.info(f"[{self.request_id}] 使用前端提供的logit_bias: {logit_bias}")
            else:
                request_params["logit_bias"] = self.config.LOGIT_BIAS
                self.logger.info(f"[{self.request_id}] 使用配置中的默认logit_bias: {self.config.LOGIT_BIAS}")
            
            # 记录请求详情
            self.logger.info(f"[{self.request_id}] === 发送API请求 ===")
            self.logger.info(f"[{self.request_id}] 请求参数:")
            self.logger.info(f"[{self.request_id}] - 模型: {model}")
            self.logger.info(f"[{self.request_id}] - 消息数量: {len(messages)}")
            self.logger.info(f"[{self.request_id}] - 温度: {request_params['temperature']}")
            self.logger.info(f"[{self.request_id}] - 最大token: {request_params['max_tokens']}")
            self.logger.info(f"[{self.request_id}] - Top-P: {request_params['top_p']}")
            
            # 记录消息内容（完整记录）
            self.logger.info(f"[{self.request_id}] === 输入消息详情 ===")
            for i, msg in enumerate(messages):
                content = msg.get('content', '')
                role = msg.get('role', 'unknown')
                self.logger.info(f"[{self.request_id}] 消息{i+1} ({role}) - 长度: {len(content)} 字符")
                
                # 按行记录消息内容
                content_lines = content.split('\n')
                for line_num, line in enumerate(content_lines, 1):
                    self.logger.info(f"[{self.request_id}] 消息{i+1}第{line_num}行: {line}")
                
                # 同时记录截断版本用于快速查看
                truncated_content = content[:200] + '...' if len(content) > 200 else content
                self.logger.info(f"[{self.request_id}] 消息{i+1} ({role}) 预览: {truncated_content}")
            self.logger.info(f"[{self.request_id}] === 输入消息详情结束 ===")
            
            # 发送API请求
            self.logger.info(f"[{self.request_id}] 正在调用OpenAI API...")
            
            # 记录完整的请求参数JSON
            self.logger.info(f"[{self.request_id}] === 完整请求参数JSON ===")
            self.logger.info(f"[{self.request_id}] {json.dumps(request_params, ensure_ascii=False, indent=2)}")
            self.logger.info(f"[{self.request_id}] === 完整请求参数JSON结束 ===")
            
            response = self.client.chat.completions.create(**request_params)
            
            # 计算请求耗时
            duration = time.time() - start_time
            
            # 记录响应详情
            self.logger.info(f"[{self.request_id}] === API响应成功 ===")
            self.logger.info(f"[{self.request_id}] 请求耗时: {duration:.2f}秒")
            
            # 记录完整的响应JSON
            self.logger.info(f"[{self.request_id}] === 完整响应JSON ===")
            try:
                # 将响应对象转换为字典格式
                response_dict = {
                    "choices": [
                        {
                            "finish_reason": choice.finish_reason,
                            "index": choice.index,
                            "logprobs": choice.logprobs,
                            "message": {
                                "content": choice.message.content,
                                "role": choice.message.role
                            }
                        } for choice in response.choices
                    ],
                    "created": getattr(response, 'created', None),
                    "id": getattr(response, 'id', 'unknown'),
                    "model": response.model,
                    "service_tier": getattr(response, 'service_tier', None),
                    "object": getattr(response, 'object', 'chat.completion'),
                    "usage": {
                        "completion_tokens": response.usage.completion_tokens,
                        "prompt_tokens": response.usage.prompt_tokens,
                        "total_tokens": response.usage.total_tokens,
                        "prompt_tokens_details": getattr(response.usage, 'prompt_tokens_details', None),
                        "completion_tokens_details": getattr(response.usage, 'completion_tokens_details', None)
                    }
                }
                self.logger.info(f"[{self.request_id}] {json.dumps(response_dict, ensure_ascii=False, indent=2)}")
            except Exception as json_error:
                self.logger.warning(f"[{self.request_id}] 无法格式化响应JSON: {str(json_error)}")
                # 备用方案：记录响应对象的字符串表示
                self.logger.info(f"[{self.request_id}] 响应对象: {str(response)}")
            self.logger.info(f"[{self.request_id}] === 完整响应JSON结束 ===")
            
            # 提取响应数据
            result = {
                'success': True,
                'content': response.choices[0].message.content,
                'model': response.model,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                'finish_reason': response.choices[0].finish_reason,
                'request_id': getattr(response, 'id', 'unknown'),
                'duration': duration
            }
            
            # 记录响应内容
            self.logger.info(f"[{self.request_id}] 响应内容长度: {len(result['content'])} 字符")
            self.logger.info(f"[{self.request_id}] 使用模型: {result['model']}")
            self.logger.info(f"[{self.request_id}] Token使用: 输入={result['usage']['prompt_tokens']}, "
                           f"输出={result['usage']['completion_tokens']}, "
                           f"总计={result['usage']['total_tokens']}")
            self.logger.info(f"[{self.request_id}] 完成原因: {result['finish_reason']}")
            self.logger.info(f"[{self.request_id}] API请求ID: {result['request_id']}")
            
            # 记录完整的模型输出内容
            self.logger.info(f"[{self.request_id}] === 模型完整输出开始 ===")
            # 按行记录，避免单行过长
            output_lines = result['content'].split('\n')
            for i, line in enumerate(output_lines, 1):
                self.logger.info(f"[{self.request_id}] 输出第{i}行: {line}")
            self.logger.info(f"[{self.request_id}] === 模型完整输出结束 ===")
            
            # 同时记录截断版本用于快速查看
            truncated_response = result['content'][:300] + '...' if len(result['content']) > 300 else result['content']
            self.logger.info(f"[{self.request_id}] 响应内容(截断预览): {truncated_response}")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            
            # 记录错误详情
            self.logger.error(f"[{self.request_id}] === API请求失败 ===")
            self.logger.error(f"[{self.request_id}] 请求耗时: {duration:.2f}秒")
            self.logger.error(f"[{self.request_id}] 错误类型: {type(e).__name__}")
            self.logger.error(f"[{self.request_id}] 错误消息: {error_msg}")
            
            # 分析错误类型
            if "401" in error_msg or "Unauthorized" in error_msg:
                self.logger.error(f"[{self.request_id}] 认证错误 - API密钥可能无效")
                if self.config.DEBUG:
                    self.logger.error(f"[{self.request_id}] API密钥: {self.api_key}")
                else:
                    self.logger.error(f"[{self.request_id}] API密钥前缀: {self.api_key[:10]}...")
                self.logger.error(f"[{self.request_id}] API密钥长度: {len(self.api_key)}")
            elif "403" in error_msg or "Forbidden" in error_msg:
                self.logger.error(f"[{self.request_id}] 权限错误 - 可能没有访问该模型的权限")
            elif "404" in error_msg or "Not Found" in error_msg:
                self.logger.error(f"[{self.request_id}] 模型不存在 - 检查模型名称: {model}")
            elif "429" in error_msg or "Rate limit" in error_msg:
                self.logger.error(f"[{self.request_id}] 速率限制 - 请求过于频繁")
            elif "500" in error_msg or "Internal Server Error" in error_msg:
                self.logger.error(f"[{self.request_id}] 服务器内部错误")
            
            return {
                'success': False,
                'error': error_msg,
                'duration': duration,
                'error_type': type(e).__name__
            }
    
    def validate_model_endpoint(self, model: str) -> bool:
        """
        验证模型端点是否有效
        
        Args:
            model: 模型名称或端点
            
        Returns:
            是否有效
        """
        if not model or len(model.strip()) < 3:
            self.logger.warning(f"[{self.request_id}] 模型名称无效: '{model}'")
            return False
        
        self.logger.info(f"[{self.request_id}] 模型验证通过: {model}")
        return True
    
    def build_messages(self, user_content: str, system_content: str = None) -> List[Dict[str, str]]:
        """
        构建消息列表
        
        Args:
            user_content: 用户消息内容
            system_content: 系统消息内容（可选）
            
        Returns:
            消息列表
        """
        messages = []
        
        # 添加系统消息
        if system_content and system_content.strip():
            messages.append({
                "role": "system",
                "content": system_content.strip()
            })
            self.logger.info(f"[{self.request_id}] 添加系统消息，长度: {len(system_content)} 字符")
        
        # 添加用户消息
        messages.append({
            "role": "user", 
            "content": user_content.strip()
        })
        self.logger.info(f"[{self.request_id}] 添加用户消息，长度: {len(user_content)} 字符")
        
        self.logger.info(f"[{self.request_id}] 构建消息列表完成，总消息数: {len(messages)}")
        return messages