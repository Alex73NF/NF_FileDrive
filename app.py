import re
import shutil
from urllib.parse import quote
import os
import logging
from datetime import datetime

from flask import Flask, session, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

def secure_filename_custom(filename):
    # 只过滤掉Windows文件系统不允许的特殊字符，保留所有合法字符（包括中文）
    invalid_chars = r'[\\/:*?"<>|\x00-\x1f]'
    filename = re.sub(invalid_chars, '', filename)
    filename = filename.strip().rstrip('.')
    return filename if filename else 'unnamed_file'

def create_app():
    app = Flask(__name__)
    
    # 配置静态文件缓存
    @app.context_processor
    def inject_version():
        return {'version': os.environ.get('VERSION', '1.0.0')}
    
    app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))  # 在生产环境中应使用更安全的密钥
    
    # 从环境变量读取配置
    PASSWORD = os.getenv('SYSTEM_PASSWORD', 'default_password')
    PASSWORD_MODE = os.getenv('PASSWORD_MODE', 'both').lower()  # 新增模式配置
    FIXED_PASSWORD = '123'  # 新增固定测试密码

    # 确保uploads目录存在
    UPLOAD_FOLDER = 'uploads'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 限制上传文件大小为100MB

    @app.route('/')
    def home():
        return render_template('login.html')  # 修改为渲染登录页面

    @app.route('/login', methods=['POST'])
    def login():
        password = request.form.get('password')

        if PASSWORD_MODE == 'env':
            valid = (password == PASSWORD)
        elif PASSWORD_MODE == 'fixed':
            valid = (password == FIXED_PASSWORD)
        elif PASSWORD_MODE == 'both':
            valid = (password == PASSWORD) or (password == FIXED_PASSWORD)
        else:
            valid = False

        if valid:
            session['logged_in'] = True
            return jsonify({'success': True})
        return jsonify({'error': '密码错误'}), 401

    @app.route('/upload.html')
    def upload_page():
        if not session.get('logged_in'):
            return jsonify({'error': '请先登录'}), 401
        return render_template('upload.html')  # 已登录时渲染上传页面

    @app.route('/upload_chunk', methods=['POST'])
    def upload_chunk():
        if not session.get('logged_in'):
            return jsonify({'error': '未授权访问'}), 401

        chunk = request.files.get('chunk')
        index = request.form.get('index')
        total = request.form.get('total')
        file_hash = request.form.get('hash')

        # 创建临时目录存储分片
        temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'temp', file_hash)
        os.makedirs(temp_dir, exist_ok=True)

        chunk.save(os.path.join(temp_dir, f'{index}.part'))
        return jsonify({'received': index})

    @app.route('/merge_files', methods=['POST'])
    def merge_files():
        file_hash = request.json.get('hash')
        filename = secure_filename_custom(request.json.get('filename'))

        temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'temp', file_hash)
        final_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        with open(final_path, 'wb') as f:
            for chunk in sorted(os.listdir(temp_dir), key=lambda x: int(x.split('.')[0])):
                with open(os.path.join(temp_dir, chunk), 'rb') as c:
                    f.write(c.read())

        # 清理临时目录
        shutil.rmtree(temp_dir)
        return jsonify({'success': True})

    @app.route('/upload', methods=['POST'])
    def upload_file():
        if not session.get('logged_in'):
            logging.warning('未授权访问尝试')
            response = jsonify({'success': False, 'error': '未授权访问'})
            response.headers['Content-Type'] = 'application/json'
            return response, 401

        if 'file' not in request.files:
            response = jsonify({'error': '没有文件被上传'})
            response.headers['Content-Type'] = 'application/json'
            return response, 400

        file = request.files['file']
        if file.filename == '':
            response = jsonify({'error': '没有选择文件'})
            response.headers['Content-Type'] = 'application/json'
            return response, 400

        try:
            # 确保文件名是字符串类型并且编码正确
            original_filename = file.filename
            if isinstance(original_filename, bytes):
                original_filename = original_filename.decode('utf-8')

            # 保存文件逻辑
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(original_filename))
            file.save(save_path)

            return jsonify({
                'success': True,
                'filename': original_filename,
                'upload_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        except Exception as e:
            logging.error(f'文件上传失败: {str(e)}')
            response = jsonify({'error': '文件上传失败'})
            response.headers['Content-Type'] = 'application/json'
            return response, 500

    @app.route('/file_list')
    def file_list():
        if not session.get('logged_in'):
            logging.warning('未授权访问尝试')
            response = jsonify({'success': False, 'error': '未授权访问'})
            response.headers['Content-Type'] = 'application/json'
            return response, 401
        try:
            files = os.listdir(app.config['UPLOAD_FOLDER'])
            return jsonify({'files': files})
        except FileNotFoundError:
            return jsonify({'error': '上传目录不存在'}), 404

    @app.route('/download')
    def download_file():
        if not session.get('logged_in'):
            return "请先登录", 401
        filename = request.args.get('filename')
        if not filename:
            return jsonify({'error': '缺少文件名参数'}), 400

        try:
            # 确保文件名是UTF-8编码
            if isinstance(filename, bytes):
                filename = filename.decode('utf-8')

            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if not os.path.exists(file_path):
                return jsonify({'error': '文件不存在'}), 404

            # 使用send_from_directory发送文件，并正确设置Content-Disposition
            response = send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

            # 使用RFC 5987编码处理中文文件名
            encoded_filename = quote(filename.encode('utf-8'))
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{encoded_filename}'

            # 设置正确的Content-Type和Content-Length
            import mimetypes
            mime_type, _ = mimetypes.guess_type(filename)
            response.headers['Content-Type'] = mime_type or 'application/octet-stream'
            response.headers['Content-Length'] = os.path.getsize(file_path)
            return response
        except Exception as e:
            return jsonify({'error': f'文件下载失败: {str(e)}'}), 500

    # 配置会话
    app.config['SESSION_COOKIE_SECURE'] = False  # 允许通过HTTP发送cookie
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # 防止JavaScript访问cookie
    app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 会话过期时间30分钟

    return app

if __name__ == '__main__':
    app = create_app()
    from waitress import serve
    serve(app, host='0.0.0.0', port=8080, threads=4)