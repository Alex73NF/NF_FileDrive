import os
from flask import Flask
from waitress import serve

# 导入自定义模块
from config import Config
from utils import setup_logger, ensure_directories
from auth import init_app as init_auth
from file_operations import init_app as init_files
from error_handlers import init_app as init_errors

def create_app(config_class=Config):
    """创建并配置Flask应用实例

    Args:
        config_class: 配置类，默认为Config

    Returns:
        配置好的Flask应用实例
    """
    # 创建Flask应用
    app = Flask(__name__)

    # 加载配置
    app.config.from_object(config_class)

    # 设置密钥
    app.secret_key = config_class.SECRET_KEY

    # 配置日志系统
    logger = setup_logger()

    # 确保必要的目录存在
    ensure_directories(app.config['UPLOAD_FOLDER'])

    # 注册上下文处理器
    @app.context_processor
    def inject_version():
        return {'version': os.environ.get('VERSION', '1.0.0')}

    # 初始化各模块
    init_auth(app, config_class)
    init_files(app)
    init_errors(app)

    # 配置安全相关的HTTP响应头
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers.pop('Expires', None)
        response.headers['Server'] = 'FileDrive'
        response.headers['text-size-adjust'] = '100%'
        response.headers['-webkit-text-size-adjust'] = '100%'
        response.headers['-ms-text-size-adjust'] = '100%'
        return response

    # 配置静态文件缓存
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = config_class.SEND_FILE_MAX_AGE_DEFAULT

    return app

if __name__ == '__main__':
    app = create_app()
    if app.config['DEBUG']:
        # 开发模式：使用Flask内置服务器
        app.run(host='0.0.0.0', port=8080, debug=True)
    else:
        # 生产模式：使用Waitress服务器
        serve(app, host='0.0.0.0', port=8080, threads=4)