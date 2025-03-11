import re
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from werkzeug.utils import secure_filename as werkzeug_secure_filename

# 配置日志系统
def setup_logger():
    """配置应用的日志系统"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('file_drive')

# 创建应用所需的目录
def ensure_directories(upload_folder: str):
    """确保应用所需的目录存在"""
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(os.path.join(upload_folder, 'temp'), exist_ok=True)

# 安全的文件名处理
def secure_filename_custom(filename: str) -> str:
    """自定义的安全文件名处理函数，保留中文字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        处理后的安全文件名
    """
    # 只过滤掉Windows文件系统不允许的特殊字符，保留所有合法字符（包括中文）
    invalid_chars = r'[\\/:*?"<>|\x00-\x1f]'
    filename = re.sub(invalid_chars, '', filename)
    filename = filename.strip().rstrip('.')
    return filename if filename else 'unnamed_file'

# 获取文件类型
def get_file_type(filename: str) -> str:
    """根据文件扩展名获取文件类型
    
    Args:
        filename: 文件名
        
    Returns:
        文件类型: image, video, audio, document, archive, other
    """
    ext = os.path.splitext(filename)[1].lower()
    
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']:
        return 'image'
    elif ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm']:
        return 'video'
    elif ext in ['.mp3', '.wav', '.ogg', '.flac', '.aac']:
        return 'audio'
    elif ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.md', '.csv']:
        return 'document'
    elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
        return 'archive'
    else:
        return 'other'

# 文件分页函数
def paginate_files(files: List[str], page: int, per_page: int) -> Dict[str, Any]:
    """对文件列表进行分页
    
    Args:
        files: 文件列表
        page: 当前页码
        per_page: 每页显示数量
        
    Returns:
        分页结果字典
    """
    total = len(files)
    total_pages = (total + per_page - 1) // per_page
    
    # 确保页码有效
    page = max(1, min(page, total_pages)) if total_pages > 0 else 1
    
    # 计算当前页的文件
    start = (page - 1) * per_page
    end = min(start + per_page, total)
    current_files = files[start:end]
    
    return {
        'files': current_files,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages
    }

# 获取文件信息
def get_file_info(file_path: str) -> Dict[str, Any]:
    """获取文件的详细信息
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件信息字典
    """
    if not os.path.exists(file_path):
        return {}
        
    filename = os.path.basename(file_path)
    stats = os.stat(file_path)
    
    return {
        'name': filename,
        'size': stats.st_size,
        'size_human': format_file_size(stats.st_size),
        'modified': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
        'type': get_file_type(filename)
    }

# 格式化文件大小
def format_file_size(size_bytes: int) -> str:
    """将字节大小转换为人类可读的格式
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        格式化后的大小字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024 or unit == 'TB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024