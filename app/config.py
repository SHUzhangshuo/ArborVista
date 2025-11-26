import os
from pathlib import Path

class Config:
    """应用配置类"""
    
    # 基础路径配置
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    INPUT_DIR = DATA_DIR / "input"
    OUTPUT_DIR = DATA_DIR / "output"
    LOGS_DIR = DATA_DIR / "logs"
    
    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB最大文件大小
    
    # 支持的文件格式
    SUPPORTED_EXTENSIONS = {
        'pdf': 'application/pdf',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg'
    }
    
    # MinerU API配置
    MINERU_API_TOKEN = os.environ.get('MINERU_API_TOKEN')
    MINERU_USE_LOCAL = os.environ.get('MINERU_USE_LOCAL', 'false').lower() == 'true'
    MINERU_LOCAL_URL = os.environ.get('MINERU_LOCAL_URL', 'http://127.0.0.1:30000')
    
    # RAG/LLM配置
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_BASE_URL = os.environ.get('OPENAI_BASE_URL', '')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-5')
    OPENAI_TEMPERATURE = float(os.environ.get('OPENAI_TEMPERATURE', '0.7'))
    
    # 向量数据库配置
    VECTOR_DB_DIR = DATA_DIR / "vectorDatabase"
    
    # 应用信息
    APP_NAME = "览树"
    APP_VERSION = "1.0.0"
    APP_DESCRIPTION = "智能论文阅读助手"
    
    @classmethod
    def init_app(cls, app):
        """初始化应用配置"""
        # 确保必要的目录存在
        cls.INPUT_DIR.mkdir(exist_ok=True)
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)
        
        # 设置Flask配置
        app.config['SECRET_KEY'] = cls.SECRET_KEY
        app.config['MAX_CONTENT_LENGTH'] = cls.MAX_CONTENT_LENGTH
        
        # 检查MinerU配置
        if cls.MINERU_USE_LOCAL:
            print("✅ MinerU 本地模式已启用")
            print(f"   本地URL: {cls.MINERU_LOCAL_URL}")
        else:
            if not cls.MINERU_API_TOKEN:
                print("⚠️ 警告: MINERU_API_TOKEN 环境变量未设置")
                print("   请在环境变量中设置 MINERU_API_TOKEN，或设置 MINERU_USE_LOCAL=true 使用本地模式")
            else:
                print("✅ MinerU API Token 已配置")
        
        # 检查OpenAI API配置（RAG功能）
        if not cls.OPENAI_API_KEY:
            print("⚠️ 警告: OPENAI_API_KEY 环境变量未设置")
            print("   RAG功能需要OPENAI_API_KEY，请在环境变量中设置")
        else:
            print("✅ OpenAI API Key 已配置")
        
        return cls

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False
    
    # 生产环境应该使用环境变量设置密钥
    SECRET_KEY = os.environ.get('SECRET_KEY')

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