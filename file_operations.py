import os
import shutil
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple
from urllib.parse import quote
from threading import Thread
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from werkzeug.utils import secure_filename

from utils import secure_filename_custom, get_file_info, paginate_files
from auth import login_required

files_bp = Blueprint('files', __name__)

# 文件上传路由
@files_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """处理文件上传请求"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件被上传'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400

    try:
        # 确保文件名是字符串类型并且编码正确
        original_filename = file.filename
        if isinstance(original_filename, bytes):
            original_filename = original_filename.decode('utf-8')

        # 保存文件逻辑
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(original_filename))
        file.save(save_path)

        # 获取文件信息
        file_info = get_file_info(save_path)

        return jsonify({
            'success': True,
            'filename': original_filename,
            'upload_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'file_info': file_info
        })
    except Exception as e:
        logging.error(f'文件上传失败: {str(e)}')
        return jsonify({'error': '文件上传失败'}), 500

# 分片上传路由
@files_bp.route('/upload_chunk', methods=['POST'])
@login_required
def upload_chunk():
    """处理分片上传请求"""
    chunk = request.files.get('chunk')
    index = request.form.get('index')
    total = request.form.get('total')
    file_hash = request.form.get('hash')

    # 创建临时目录存储分片
    temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp', file_hash)
    os.makedirs(temp_dir, exist_ok=True)

    chunk.save(os.path.join(temp_dir, f'{index}.part'))
    return jsonify({
        'received': index,
        'progress': f'{int(index) + 1}/{total}'
    })

# 合并文件路由
@files_bp.route('/merge_files', methods=['POST'])
@login_required
def merge_files():
    """处理文件合并请求，异步执行"""
    file_hash = request.json.get('hash')
    filename = secure_filename_custom(request.json.get('filename'))

    # 启动异步线程执行合并操作
    thread = Thread(target=_merge_file_async, args=(file_hash, filename))
    thread.daemon = True
    thread.start()

    return jsonify({
        'success': True,
        'message': '文件合并已开始，请稍候...',
        'filename': filename
    })

def _merge_file_async(file_hash: str, filename: str) -> None:
    """异步合并文件

    Args:
        file_hash: 文件哈希值
        filename: 文件名
    """
    try:
        temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp', file_hash)
        final_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        with open(final_path, 'wb') as f:
            for chunk in sorted(os.listdir(temp_dir), key=lambda x: int(x.split('.')[0])):
                with open(os.path.join(temp_dir, chunk), 'rb') as c:
                    f.write(c.read())

        # 清理临时目录
        shutil.rmtree(temp_dir)
        logging.info(f'文件 {filename} 合并完成')
    except Exception as e:
        logging.error(f'文件合并失败: {str(e)}')

# 文件列表路由
@files_bp.route('/file_list')
@login_required
def file_list():
    """获取文件列表，支持分页"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', current_app.config.get('FILES_PER_PAGE', 10)))

        # 获取所有文件
        all_files = []
        upload_folder = current_app.config['UPLOAD_FOLDER']

        for filename in os.listdir(upload_folder):
            file_path = os.path.join(upload_folder, filename)
            if os.path.isfile(file_path) and not filename.startswith('.'):
                file_info = get_file_info(file_path)
                all_files.append(file_info)

        # 按修改时间排序
        all_files.sort(key=lambda x: x.get('modified', ''), reverse=True)

        # 分页处理
        paginated = paginate_files(all_files, page, per_page)

        return jsonify(paginated)
    except FileNotFoundError:
        return jsonify({'error': '上传目录不存在'}), 404
    except Exception as e:
        logging.error(f'获取文件列表失败: {str(e)}')
        return jsonify({'error': f'获取文件列表失败: {str(e)}'}), 500

# 文件下载路由
@files_bp.route('/download')
@login_required
def download_file():
    """处理文件下载请求"""
    filename = request.args.get('filename')
    if not filename:
        return jsonify({'error': '缺少文件名参数'}), 400

    try:
        # 确保文件名是UTF-8编码
        if isinstance(filename, bytes):
            filename = filename.decode('utf-8')

        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404

        # 使用send_from_directory发送文件，并正确设置Content-Disposition
        response = send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

        # 使用RFC 5987编码处理中文文件名
        encoded_filename = quote(filename.encode('utf-8'))
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{encoded_filename}'

        # 设置正确的Content-Type和Content-Length
        import mimetypes
        mime_type, _ = mimetypes.guess_type(filename)
        response.headers['Content-Type'] = mime_type or 'application/octet-stream'
        response.headers['Content-Length'] = os.path.getsize(file_path)

        # 记录下载日志
        logging.info(f'文件下载: {filename}')

        return response
    except Exception as e:
        logging.error(f'文件下载失败: {str(e)}')
        return jsonify({'error': f'文件下载失败: {str(e)}'}), 500

# 文件删除路由
@files_bp.route('/delete', methods=['DELETE'])
@login_required
def delete_file():
    """处理文件删除请求"""
    filename = request.json.get('filename')
    if not filename:
        return jsonify({'error': '缺少文件名参数'}), 400

    try:
        # 使用current_app.config来获取配置，而不是files_bp.config
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404

        os.remove(file_path)
        logging.info(f'文件删除: {filename}')
        return jsonify({'success': True, 'message': f'文件 {filename} 已删除'})
    except Exception as e:
        logging.error(f'文件删除失败: {str(e)}')
        return jsonify({'error': f'文件删除失败: {str(e)}'}), 500

# 文件预览路由
@files_bp.route('/preview')
@login_required
def preview_file():
    """处理文件预览请求"""
    filename = request.args.get('filename')
    if not filename:
        return jsonify({'error': '缺少文件名参数'}), 400

    try:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404

        # 获取文件类型
        file_info = get_file_info(file_path)
        file_type = file_info.get('type')

        # 根据文件类型返回不同的预览信息
        preview_data = {
            'name': filename,
            'type': file_type,
            'size': file_info.get('size_human'),
            'modified': file_info.get('modified'),
            'preview_url': f'/raw/{filename}' if file_type == 'image' else None
        }

        return jsonify(preview_data)
    except Exception as e:
        logging.error(f'文件预览失败: {str(e)}')
        return jsonify({'error': f'文件预览失败: {str(e)}'}), 500

# 原始文件访问路由（用于预览）
@files_bp.route('/raw/<path:filename>')
@login_required
def raw_file(filename):
    """提供原始文件访问，用于预览"""
    try:
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        logging.error(f'访问原始文件失败: {str(e)}')
        return jsonify({'error': f'访问文件失败: {str(e)}'}), 500



def init_app(app):
    """初始化文件操作模块

    Args:
        app: Flask应用实例
    """
    files_bp.config = app.config
    app.register_blueprint(files_bp, url_prefix='/files')

    # 注册直接路由
    app.add_url_rule('/upload', view_func=upload_file, methods=['POST'])
    app.add_url_rule('/upload_chunk', view_func=upload_chunk, methods=['POST'])
    app.add_url_rule('/merge_files', view_func=merge_files, methods=['POST'])
    app.add_url_rule('/file_list', view_func=file_list)
    app.add_url_rule('/download', view_func=download_file)
    app.add_url_rule('/delete', view_func=delete_file, methods=['DELETE'])
    app.add_url_rule('/preview', view_func=preview_file)
    app.add_url_rule('/raw/<path:filename>', view_func=raw_file)

    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'temp'), exist_ok=True)




