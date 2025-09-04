import os
from pathlib import Path

class Config:
    """应用配置类"""
    
    # 基础路径配置
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    INPUT_DIR = DATA_DIR / "input"
    OUTPUT_DIR = DATA_DIR / "output"
    
    # MinerU客户端路径
    CLIENT_SCRIPT = BASE_DIR / "mineru" / "cli" / "client.py"
    
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
    
    # MinerU处理配置
    MINERU_CONFIG = {
        'method': 'auto',
        'backend': 'pipeline',
        'language': 'ch',
        'formula_enable': True,
        'table_enable': True,
        'device_mode': 'cuda:0',  # GPU设备：cuda:0, cuda:1, cpu, npu等
        'virtual_vram': 7168,     # GPU内存限制：8GB GPU建议设置为7168MB
        'model_source': 'huggingface'  # 模型源：huggingface, modelscope, local
    }
    
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
        
        # 设置Flask配置
        app.config['SECRET_KEY'] = cls.SECRET_KEY
        app.config['MAX_CONTENT_LENGTH'] = cls.MAX_CONTENT_LENGTH
        
        # 设置MinerU GPU环境变量
        cls._setup_mineru_environment()
        
        return cls
    
    @classmethod
    def _setup_mineru_environment(cls):
        """设置MinerU GPU环境变量"""
        # 设置设备模式
        if os.environ.get('MINERU_DEVICE_MODE') is None:
            os.environ['MINERU_DEVICE_MODE'] = cls.MINERU_CONFIG['device_mode']
        
        # 设置GPU内存限制
        if os.environ.get('MINERU_VIRTUAL_VRAM_SIZE') is None:
            os.environ['MINERU_VIRTUAL_VRAM_SIZE'] = str(cls.MINERU_CONFIG['virtual_vram'])
        
        # 设置模型源
        if os.environ.get('MINERU_MODEL_SOURCE') is None:
            os.environ['MINERU_MODEL_SOURCE'] = cls.MINERU_CONFIG['model_source']
        
        # 打印环境变量设置信息
        print(f"🎯 MinerU GPU 配置已设置:")
        print(f"   📱 设备模式: {os.environ['MINERU_DEVICE_MODE']}")
        print(f"   💾 GPU内存: {os.environ['MINERU_VIRTUAL_VRAM_SIZE']}MB")
        print(f"   📦 模型源: {os.environ['MINERU_MODEL_SOURCE']}")

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
