"""
服务器端口映射配置
直接修改此文件中的变量即可，无需配置环境变量
"""

# 后端端口配置
BACKEND_PORT = 6006
FRONTEND_PORT = 6008

# 端口映射配置（本地端口 -> 服务器URL）
PORT_MAPPING = {
    '6006': 'https://u486956-b5fb-82b008e7.westb.seetacloud.com:8443',
    '6008': 'https://uu486956-b5fb-82b008e7.westb.seetacloud.com:8443',
}

def get_server_url(local_port):
    """
    根据本地端口获取服务器映射URL
    
    Args:
        local_port: 本地端口号（字符串或整数）
        
    Returns:
        服务器URL，如果未配置则返回None
    """
    return PORT_MAPPING.get(str(local_port))

