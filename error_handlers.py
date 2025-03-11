from flask import Blueprint, jsonify, render_template
import logging

error_bp = Blueprint('errors', __name__)

# 404错误 - 资源未找到
@error_bp.app_errorhandler(404)
def not_found_error(error):
    """处理404错误"""
    if request_wants_json():
        return jsonify({'error': '请求的资源不存在'}), 404
    return render_template('errors/404.html'), 404

# 401错误 - 未授权
@error_bp.app_errorhandler(401)
def unauthorized_error(error):
    """处理401错误"""
    if request_wants_json():
        return jsonify({'error': '未授权访问'}), 401
    return render_template('errors/401.html'), 401

# 403错误 - 禁止访问
@error_bp.app_errorhandler(403)
def forbidden_error(error):
    """处理403错误"""
    if request_wants_json():
        return jsonify({'error': '禁止访问此资源'}), 403
    return render_template('errors/403.html'), 403

# 500错误 - 服务器内部错误
@error_bp.app_errorhandler(500)
def internal_error(error):
    """处理500错误"""
    logging.error(f'服务器错误: {str(error)}')
    if request_wants_json():
        return jsonify({'error': '服务器内部错误'}), 500
    return render_template('errors/500.html'), 500

# 413错误 - 请求实体过大
@error_bp.app_errorhandler(413)
def request_entity_too_large(error):
    """处理413错误 - 文件过大"""
    if request_wants_json():
        return jsonify({'error': '上传的文件超过了允许的大小限制'}), 413
    return render_template('errors/413.html'), 413

# 判断请求是否期望JSON响应
def request_wants_json():
    """判断请求是否期望JSON响应"""
    from flask import request
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > request.accept_mimetypes['text/html']

def init_app(app):
    """初始化错误处理模块
    
    Args:
        app: Flask应用实例
    """
    app.register_blueprint(error_bp)
    
    # 注册全局错误处理器
    app.register_error_handler(404, not_found_error)
    app.register_error_handler(401, unauthorized_error)
    app.register_error_handler(403, forbidden_error)
    app.register_error_handler(500, internal_error)
    app.register_error_handler(413, request_entity_too_large)