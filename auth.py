from flask import Blueprint, render_template, request, session, jsonify
from functools import wraps
import logging

auth_bp = Blueprint('auth', __name__)

# 认证装饰器
def login_required(f):
    """验证用户是否已登录的装饰器
    
    如果用户未登录，返回401未授权错误
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            logging.warning('未授权访问尝试')
            return jsonify({'error': '请先登录'}), 401
        return f(*args, **kwargs)
    return decorated_function

# 登录路由
@auth_bp.route('/login', methods=['POST'])
def login():
    """处理用户登录请求"""
    password = request.form.get('password')
    config = auth_bp.config
    
    # 仅使用环境变量中的密码进行验证
    valid = (password == config['PASSWORD'])
    
    if valid:
        session['logged_in'] = True
        return jsonify({'success': True})
    return jsonify({'error': '密码错误'}), 401

# 登出路由
@auth_bp.route('/logout')
def logout():
    """处理用户登出请求"""
    session.pop('logged_in', None)
    return jsonify({'success': True})

# 登录页面
@auth_bp.route('/')
def login_page():
    """渲染登录页面"""
    return render_template('login.html')

# 上传页面
@auth_bp.route('/upload.html')
@login_required
def upload_page():
    """渲染上传页面，需要登录"""
    return render_template('upload.html')

def init_app(app, config):
    """初始化认证模块
    
    Args:
        app: Flask应用实例
        config: 配置字典
    """
    auth_bp.config = {
        'PASSWORD': config.PASSWORD,
        'PASSWORD_MODE': config.PASSWORD_MODE
    }
    app.register_blueprint(auth_bp)