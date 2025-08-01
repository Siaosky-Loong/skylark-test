"""
应用配置文件
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """基础配置类"""
    
    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_PORT', 8001))
    
    # BytePlus ModelArk配置
    ARK_API_KEY = os.environ.get('ARK_API_KEY')
    ARK_BASE_URL = os.environ.get('ARK_BASE_URL', 'https://ark.cn-beijing.volces.com/api/v3')
    
    # 模型默认参数
    DEFAULT_TEMPERATURE = float(os.environ.get('DEFAULT_TEMPERATURE', 1.0))
    DEFAULT_MAX_TOKENS = int(os.environ.get('DEFAULT_MAX_TOKENS', 1000))
    DEFAULT_TOP_P = float(os.environ.get('DEFAULT_TOP_P', 0.7))
    DEFAULT_FREQUENCY_PENALTY = float(os.environ.get('DEFAULT_FREQUENCY_PENALTY', 0.1))
    DEFAULT_PRESENCE_PENALTY = float(os.environ.get('DEFAULT_PRESENCE_PENALTY', 0.1))
    
    # Logit Bias配置 - 按照文档要求配置
    # 可以通过环境变量LOGIT_BIAS_JSON覆盖，格式为JSON字符串
    DEFAULT_LOGIT_BIAS = {
        "861": -100,
        "854": -100,
        "135": -100,
        "136": -100
    }
    
    # 从环境变量读取logit_bias配置，如果没有则使用默认值
    try:
        import json
        logit_bias_env = os.environ.get('LOGIT_BIAS_JSON')
        if logit_bias_env:
            LOGIT_BIAS = json.loads(logit_bias_env)
        else:
            LOGIT_BIAS = DEFAULT_LOGIT_BIAS
    except (json.JSONDecodeError, ValueError) as e:
        print(f"警告: LOGIT_BIAS_JSON环境变量格式错误，使用默认值: {e}")
        LOGIT_BIAS = DEFAULT_LOGIT_BIAS
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """获取当前配置"""
    env = os.environ.get('FLASK_ENV', 'default')
    return config.get(env, config['default'])