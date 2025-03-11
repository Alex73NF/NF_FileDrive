import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

class Config:
    """应用配置类"""
    # 基础配置
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', os.urandom(24))
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'  # 从环境变量读取调试模式配置

    # 上传配置
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB

    # 认证配置
    PASSWORD = os.getenv('SYSTEM_PASSWORD', 'default_password')
    PASSWORD_MODE = os.getenv('PASSWORD_MODE', 'env').lower()

    # 会话配置
    SESSION_COOKIE_SECURE = False  # 允许通过HTTP发送cookie
    SESSION_COOKIE_HTTPONLY = True  # 防止JavaScript访问cookie
    PERMANENT_SESSION_LIFETIME = 1800  # 会话过期时间30分钟

    # 缓存配置
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 静态文件缓存1年

    # 分页配置
    FILES_PER_PAGE = 10