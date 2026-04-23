import os
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from langchain_core.tools import tool
from .security import SecurityValidator
from .config import system_config
from app.core import registry

@registry.register_tool
@tool
def get_project_status(project_path: str = "") -> Dict[str, Any]:
    """
    获取项目状态信息

    Args:
        project_path: 项目子路径，默认为根目录
    """
    try:
        # 验证路径安全性
        is_safe, abs_path, error = SecurityValidator.validate_path(project_path)
        if not is_safe:
            return {"success": False, "error": error}

        if not os.path.exists(abs_path):
            return {"success": False, "error": f"路径不存在: {project_path}"}

        status = {
            "success": True,
            "path": project_path,
            "absolute_path": abs_path,
            "scan_time": datetime.now().isoformat(),
            "is_directory": os.path.isdir(abs_path),
            "stats": _get_path_stats(abs_path)
        }

        if os.path.isdir(abs_path):
            # 目录信息
            status["directory_info"] = _analyze_directory(abs_path)
        else:
            # 文件信息
            status["file_info"] = _analyze_file(abs_path)

        return status

    except Exception as e:
        return {"success": False, "error": f"获取项目状态失败: {str(e)}"}

@registry.register_tool
@tool
def list_project_files(directory: str = "", recursive: bool = True, file_types: List[str] = None) -> Dict[str, Any]:
    """
    列出项目文件

    Args:
        directory: 要列出的目录
        recursive: 是否递归列出子目录
        file_types: 文件类型过滤 (如: ['.js', '.css', '.html'])
    """
    try:
        # 验证路径安全性
        is_safe, abs_path, error = SecurityValidator.validate_path(directory)
        if not is_safe:
            return {"success": False, "error": error}

        if not os.path.exists(abs_path):
            return {"success": False, "error": f"目录不存在: {directory}"}

        if not os.path.isdir(abs_path):
            return {"success": False, "error": f"路径不是目录: {directory}"}

        files = []
        directories = []

        if recursive:
            for root, dirs, filenames in os.walk(abs_path):
                # 添加目录
                for dir_name in dirs:
                    dir_path = os.path.relpath(os.path.join(root, dir_name), abs_path)
                    directories.append({
                        "name": dir_name,
                        "path": dir_path,
                        "type": "directory"
                    })

                # 添加文件
                for filename in filenames:
                    file_path = os.path.relpath(os.path.join(root, filename), abs_path)
                    if _should_include_file(filename, file_types):
                        files.append(_get_file_info(os.path.join(root, filename), file_path))
        else:
            # 只列出当前目录
            for item in os.listdir(abs_path):
                item_path = os.path.join(abs_path, item)
                rel_path = os.path.relpath(item_path, abs_path)

                if os.path.isdir(item_path):
                    directories.append({
                        "name": item,
                        "path": rel_path,
                        "type": "directory"
                    })
                else:
                    if _should_include_file(item, file_types):
                        files.append(_get_file_info(item_path, rel_path))

        return {
            "success": True,
            "directory": directory,
            "total_files": len(files),
            "total_directories": len(directories),
            "files": files,
            "directories": directories,
            "scan_time": datetime.now().isoformat()
        }

    except Exception as e:
        return {"success": False, "error": f"列出文件失败: {str(e)}"}

@registry.register_tool
@tool
def analyze_project_structure(root_directory: str = "") -> Dict[str, Any]:
    """
    分析项目结构

    Args:
        root_directory: 项目根目录
    """
    try:
        # 验证路径安全性
        is_safe, abs_path, error = SecurityValidator.validate_path(root_directory)
        if not is_safe:
            return {"success": False, "error": error}

        if not os.path.exists(abs_path):
            return {"success": False, "error": f"目录不存在: {root_directory}"}

        analysis = {
            "success": True,
            "project_root": root_directory,
            "analysis_time": datetime.now().isoformat(),
            "structure": _analyze_project_structure_recursive(abs_path),
            "summary": _generate_structure_summary(abs_path),
            "recommendations": _generate_recommendations(abs_path)
        }

        return analysis

    except Exception as e:
        return {"success": False, "error": f"分析项目结构失败: {str(e)}"}

@registry.register_tool
@tool
def monitor_file_changes(file_path: str, last_modified: str = None) -> Dict[str, Any]:
    """
    监控文件变化

    Args:
        file_path: 要监控的文件路径
        last_modified: 上次检查的修改时间 (ISO格式)
    """
    try:
        # 验证路径安全性
        is_safe, abs_path, error = SecurityValidator.validate_path(file_path)
        if not is_safe:
            return {"success": False, "error": error}

        if not os.path.exists(abs_path):
            return {"success": False, "error": f"文件不存在: {file_path}"}

        if not os.path.isfile(abs_path):
            return {"success": False, "error": f"路径不是文件: {file_path}"}

        current_mtime = os.path.getmtime(abs_path)
        current_modified = datetime.fromtimestamp(current_mtime).isoformat()

        has_changed = True
        if last_modified:
            try:
                last_mtime = datetime.fromisoformat(last_modified).timestamp()
                has_changed = current_mtime > last_mtime
            except:
                # 如果时间格式无效，认为有变化
                has_changed = True

        file_info = _get_file_info(abs_path, file_path)
        file_info["has_changed"] = has_changed
        file_info["last_checked"] = datetime.now().isoformat()
        file_info["current_modified"] = current_modified

        return {
            "success": True,
            "file_path": file_path,
            "change_detected": has_changed,
            "file_info": file_info
        }

    except Exception as e:
        return {"success": False, "error": f"监控文件变化失败: {str(e)}"}

@registry.register_tool
@tool
def get_project_statistics(directory: str = "") -> Dict[str, Any]:
    """
    获取项目统计信息

    Args:
        directory: 项目目录
    """
    try:
        # 验证路径安全性
        is_safe, abs_path, error = SecurityValidator.validate_path(directory)
        if not is_safe:
            return {"success": False, "error": error}

        if not os.path.exists(abs_path):
            return {"success": False, "error": f"目录不存在: {directory}"}

        stats = {
            "success": True,
            "directory": directory,
            "scan_time": datetime.now().isoformat(),
            "total_stats": _calculate_directory_stats(abs_path),
            "file_type_stats": _analyze_file_types(abs_path),
            "size_analysis": _analyze_directory_sizes(abs_path)
        }

        return stats

    except Exception as e:
        return {"success": False, "error": f"获取项目统计失败: {str(e)}"}

def _get_path_stats(path: str) -> Dict[str, Any]:
    """获取路径统计信息"""
    try:
        stat = os.stat(path)
        return {
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
            "mode": stat.st_mode
        }
    except:
        return {}

def _analyze_directory(directory: str) -> Dict[str, Any]:
    """分析目录内容"""
    try:
        items = os.listdir(directory)
        files = []
        subdirs = []

        for item in items:
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                subdirs.append(item)
            else:
                files.append(item)

        return {
            "total_items": len(items),
            "file_count": len(files),
            "directory_count": len(subdirs),
            "files": files[:10],  # 限制返回数量
            "directories": subdirs[:10],
            "has_more_files": len(files) > 10,
            "has_more_directories": len(subdirs) > 10
        }
    except:
        return {}

def _analyze_file(file_path: str) -> Dict[str, Any]:
    """分析文件信息"""
    try:
        stat = os.stat(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()

        return {
            "name": os.path.basename(file_path),
            "extension": file_ext,
            "size": stat.st_size,
            "size_human": _format_file_size(stat.st_size),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "is_text_file": _is_text_file_extension(file_ext)
        }
    except:
        return {}

def _get_file_info(file_path: str, relative_path: str) -> Dict[str, Any]:
    """获取文件详细信息"""
    try:
        stat = os.stat(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()

        return {
            "name": os.path.basename(file_path),
            "path": relative_path,
            "extension": file_ext,
            "size": stat.st_size,
            "size_human": _format_file_size(stat.st_size),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "is_text_file": _is_text_file_extension(file_ext)
        }
    except:
        return {
            "name": os.path.basename(file_path),
            "path": relative_path,
            "error": "无法获取文件信息"
        }

def _should_include_file(filename: str, file_types: List[str] = None) -> bool:
    """判断是否应该包含文件"""
    if not file_types:
        return True

    file_ext = os.path.splitext(filename)[1].lower()
    return file_ext in file_types

def _is_text_file_extension(extension: str) -> bool:
    """判断是否为文本文件扩展名"""
    text_extensions = {'.txt', '.md', '.js', '.ts', '.jsx', '.tsx', '.html', '.css',
                      '.json', '.xml', '.yml', '.yaml', '.py', '.java', '.c', '.cpp',
                      '.h', '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt'}
    return extension in text_extensions

def _format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def _analyze_project_structure_recursive(directory: str, base_path: str = "") -> Dict[str, Any]:
    """递归分析项目结构"""
    try:
        structure = {}
        items = os.listdir(directory)

        for item in items:
            if item.startswith('.'):  # 跳过隐藏文件
                continue

            item_path = os.path.join(directory, item)
            rel_path = os.path.relpath(item_path, base_path or directory)

            if os.path.isdir(item_path):
                structure[item] = {
                    "type": "directory",
                    "contents": _analyze_project_structure_recursive(item_path, base_path or directory)
                }
            else:
                structure[item] = {
                    "type": "file",
                    "extension": os.path.splitext(item)[1].lower(),
                    "size": os.path.getsize(item_path)
                }

        return structure
    except:
        return {}

def _generate_structure_summary(directory: str) -> Dict[str, Any]:
    """生成结构摘要"""
    try:
        total_files = 0
        total_dirs = 0
        total_size = 0
        extension_count = {}

        for root, dirs, files in os.walk(directory):
            total_dirs += len(dirs)
            for file in files:
                if not file.startswith('.'):
                    total_files += 1
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)

                    ext = os.path.splitext(file)[1].lower()
                    extension_count[ext] = extension_count.get(ext, 0) + 1

        return {
            "total_files": total_files,
            "total_directories": total_dirs,
            "total_size": total_size,
            "total_size_human": _format_file_size(total_size),
            "file_types": extension_count
        }
    except:
        return {}

def _generate_recommendations(directory: str) -> List[str]:
    """生成项目建议"""
    recommendations = []

    try:
        # 检查常见项目文件
        common_files = ['package.json', 'README.md', '.gitignore', 'LICENSE']
        missing_files = []

        for file in common_files:
            if not os.path.exists(os.path.join(directory, file)):
                missing_files.append(file)

        if missing_files:
            recommendations.append(f"建议添加缺失的项目文件: {', '.join(missing_files)}")

        # 检查文件大小
        large_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                size = os.path.getsize(file_path)
                if size > 1024 * 1024:  # 1MB
                    rel_path = os.path.relpath(file_path, directory)
                    large_files.append(f"{rel_path} ({_format_file_size(size)})")

        if large_files:
            recommendations.append(f"发现大文件，考虑优化: {', '.join(large_files[:5])}")

    except:
        pass

    return recommendations

def _calculate_directory_stats(directory: str) -> Dict[str, Any]:
    """计算目录统计信息"""
    try:
        total_files = 0
        total_size = 0
        max_depth = 0

        for root, dirs, files in os.walk(directory):
            depth = root.replace(directory, '').count(os.sep)
            max_depth = max(max_depth, depth)

            for file in files:
                if not file.startswith('.'):
                    total_files += 1
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)

        return {
            "total_files": total_files,
            "total_size": total_size,
            "total_size_human": _format_file_size(total_size),
            "max_depth": max_depth
        }
    except:
        return {}

def _analyze_file_types(directory: str) -> Dict[str, Any]:
    """分析文件类型分布"""
    try:
        extension_stats = {}

        for root, dirs, files in os.walk(directory):
            for file in files:
                if not file.startswith('.'):
                    ext = os.path.splitext(file)[1].lower()
                    file_path = os.path.join(root, file)
                    size = os.path.getsize(file_path)

                    if ext not in extension_stats:
                        extension_stats[ext] = {"count": 0, "total_size": 0}

                    extension_stats[ext]["count"] += 1
                    extension_stats[ext]["total_size"] += size

        # 添加人类可读的大小
        for ext in extension_stats:
            extension_stats[ext]["total_size_human"] = _format_file_size(extension_stats[ext]["total_size"])

        return extension_stats
    except:
        return {}

def _analyze_directory_sizes(directory: str) -> Dict[str, Any]:
    """分析目录大小分布"""
    try:
        dir_sizes = {}

        for root, dirs, files in os.walk(directory):
            dir_size = 0
            for file in files:
                if not file.startswith('.'):
                    file_path = os.path.join(root, file)
                    dir_size += os.path.getsize(file_path)

            if dir_size > 0:
                rel_path = os.path.relpath(root, directory)
                dir_sizes[rel_path] = {
                    "size": dir_size,
                    "size_human": _format_file_size(dir_size)
                }

        # 按大小排序
        sorted_dirs = sorted(dir_sizes.items(), key=lambda x: x[1]["size"], reverse=True)

        return {
            "directory_sizes": dict(sorted_dirs[:10]),  # 返回最大的10个目录
            "total_directories_with_files": len(dir_sizes)
        }
    except:
        return {}