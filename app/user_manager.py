"""
用户管理模块
- 用户注册、登录
- 用户唯一ID生成
- 用户信息存储在TXT文件中
"""
import os
import uuid
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict


class UserManager:
    """用户管理器"""
    
    def __init__(self, users_file: str = "data/users.txt"):
        """
        初始化用户管理器
        
        Args:
            users_file: 用户信息存储文件路径
        """
        self.users_file = Path(users_file)
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        self._users_cache = None
        self._load_users()
    
    def _load_users(self):
        """从文件加载用户信息"""
        if self._users_cache is None:
            self._users_cache = {}
            if self.users_file.exists():
                try:
                    with open(self.users_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if not line or line.startswith('#'):
                                continue
                            try:
                                user_data = json.loads(line)
                                user_id = user_data.get('user_id')
                                if user_id:
                                    self._users_cache[user_id] = user_data
                            except json.JSONDecodeError:
                                continue
                except Exception as e:
                    print(f"⚠️ 加载用户信息失败: {str(e)}")
                    self._users_cache = {}
    
    def _save_user(self, user_data: Dict):
        """保存用户信息到文件"""
        try:
            with open(self.users_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(user_data, ensure_ascii=False) + '\n')
            # 更新缓存
            self._users_cache[user_data['user_id']] = user_data
        except Exception as e:
            print(f"⚠️ 保存用户信息失败: {str(e)}")
            raise
    
    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def _generate_user_id(self) -> str:
        """生成唯一用户ID"""
        return f"user_{uuid.uuid4().hex[:12]}"
    
    def register(self, username: str, password: str) -> Dict:
        """
        用户注册
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            用户信息字典，包含user_id、username等
        """
        # 检查用户名是否已存在
        for user_data in self._users_cache.values():
            if user_data.get('username') == username:
                raise ValueError("用户名已存在")
        
        # 生成用户ID
        user_id = self._generate_user_id()
        
        # 创建用户数据，初始化API配置为空字符串
        user_data = {
            'user_id': user_id,
            'username': username,
            'password_hash': self._hash_password(password),
            'created_at': datetime.now().isoformat(),
            'last_login': None,
            # 初始化API配置为空字符串
            'openai_api_key': '',
            'openai_base_url': '',
            'openai_model': '',
            'openai_temperature': '',
            'mineru_api_token': ''
        }
        
        # 保存用户
        self._save_user(user_data)
        
        return {
            'user_id': user_id,
            'username': username,
            'created_at': user_data['created_at']
        }
    
    def login(self, username: str, password: str) -> Optional[Dict]:
        """
        用户登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            用户信息字典，如果登录失败返回None
        """
        password_hash = self._hash_password(password)
        
        # 查找用户
        for user_data in self._users_cache.values():
            if (user_data.get('username') == username and 
                user_data.get('password_hash') == password_hash):
                # 更新最后登录时间
                user_data['last_login'] = datetime.now().isoformat()
                self._update_user(user_data)
                return {
                    'user_id': user_data['user_id'],
                    'username': user_data['username'],
                    'created_at': user_data.get('created_at'),
                    'last_login': user_data['last_login']
                }
        
        return None
    
    def _update_user(self, user_data: Dict):
        """更新用户信息（重新写入整个文件）"""
        try:
            # 更新缓存
            self._users_cache[user_data['user_id']] = user_data
            
            # 重新写入文件
            with open(self.users_file, 'w', encoding='utf-8') as f:
                for user in self._users_cache.values():
                    f.write(json.dumps(user, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"⚠️ 更新用户信息失败: {str(e)}")
            raise
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """
        根据用户ID获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户信息字典，如果不存在返回None
        """
        return self._users_cache.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """
        根据用户名获取用户信息
        
        Args:
            username: 用户名
            
        Returns:
            用户信息字典，如果不存在返回None
        """
        for user_data in self._users_cache.values():
            if user_data.get('username') == username:
                return user_data
        return None
    
    def verify_user_id(self, user_id: str) -> bool:
        """
        验证用户ID是否存在
        
        Args:
            user_id: 用户ID
            
        Returns:
            如果用户存在返回True，否则返回False
        """
        return user_id in self._users_cache
    
    def update_user_config(
        self, 
        user_id: str, 
        openai_api_key: str = None, 
        openai_base_url: str = None,
        openai_model: str = None,
        openai_temperature: str = None,
        mineru_api_token: str = None
    ):
        """
        更新用户API配置
        
        Args:
            user_id: 用户ID
            openai_api_key: OpenAI API密钥（可选）
            openai_base_url: OpenAI API基础URL（可选）
            openai_model: OpenAI 模型名称（可选）
            openai_temperature: OpenAI 温度参数（可选）
            mineru_api_token: MinerU API令牌（可选）
        """
        user_data = self.get_user_by_id(user_id)
        if not user_data:
            raise ValueError("用户不存在")
        
        if openai_api_key is not None:
            user_data['openai_api_key'] = openai_api_key
        if openai_base_url is not None:
            user_data['openai_base_url'] = openai_base_url
        if openai_model is not None:
            user_data['openai_model'] = openai_model
        if openai_temperature is not None:
            user_data['openai_temperature'] = openai_temperature
        if mineru_api_token is not None:
            user_data['mineru_api_token'] = mineru_api_token
        
        self._update_user(user_data)


# 全局用户管理器实例
_user_manager = None

def get_user_manager() -> UserManager:
    """获取全局用户管理器实例"""
    global _user_manager
    if _user_manager is None:
        _user_manager = UserManager()
    return _user_manager

