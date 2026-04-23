import os
import shutil
import json
from datetime import datetime
from typing import Dict, List, Any
from langchain_core.tools import tool
from .security import SecurityValidator
from .config import system_config
from app.core import registry

@registry.register_tool
@tool
def save_generated_code(file_path: str, code_content: str, file_type: str = None) -> Dict[str, Any]:
    """
    保存大模型生成的代码文件

    Args:
        file_path: 相对路径 (如: "src/components/Header.js")
        code_content: 生成的代码内容
        file_type: 文件类型 (html/css/js/json)

    Returns:
        操作结果
    """
    try:
        # 1. 路径安全验证
        is_safe, abs_path, error = SecurityValidator.validate_path(file_path)
        if not is_safe:
            return {"success": False, "error": error}

        # 2. 文件大小验证
        is_safe, error = SecurityValidator.validate_file_size(abs_path, code_content)
        if not is_safe:
            return {"success": False, "error": error}

        # 3. 创建父目录
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        # 4. 备份现有文件
        backup_path = None
        if os.path.exists(abs_path):
            backup_path = f"{abs_path}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
            shutil.copy2(abs_path, backup_path)

        # 5. 写入文件
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(code_content)

        # 6. 基础验证
        validation = _validate_file_content(abs_path, code_content, file_type)

        return {
            "success": True,
            "saved_path": file_path,
            "absolute_path": abs_path,
            "file_size": len(code_content),
            "backup_created": backup_path is not None,
            "backup_path": backup_path,
            "validation": validation
        }

    except Exception as e:
        return {"success": False, "error": f"文件保存失败: {str(e)}"}

@registry.register_tool
@tool
def read_project_file(file_path: str, max_size: int = 512000) -> Dict[str, Any]:
    """
    读取项目文件内容

    Args:
        file_path: 文件相对路径
        max_size: 最大读取大小限制
    """
    try:
        # 1. 路径安全验证
        is_safe, abs_path, error = SecurityValidator.validate_path(file_path)
        if not is_safe:
            return {"success": False, "error": error}

        # 2. 检查文件是否存在
        if not os.path.exists(abs_path):
            return {"success": False, "error": f"文件不存在: {file_path}"}

        # 3. 检查文件大小
        file_size = os.path.getsize(abs_path)
        if file_size > max_size:
            return {"success": False, "error": f"文件过大: {file_size} > {max_size}"}

        # 4. 读取文件内容
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return {
            "success": True,
            "content": content,
            "encoding": "utf-8",
            "size": file_size,
            "last_modified": datetime.fromtimestamp(os.path.getmtime(abs_path)).isoformat(),
            "is_text_file": _is_text_file(content)
        }

    except Exception as e:
        return {"success": False, "error": f"文件读取失败: {str(e)}"}

@registry.register_tool
@tool
def create_project_structure(structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    创建项目文件结构

    Args:
        structure: 项目结构定义
    """
    try:
        created_files = []
        created_dirs = []
        failed_operations = []

        def _create_recursive(current_structure, base_path=""):
            for name, content in current_structure.items():
                current_path = f"{base_path}/{name}" if base_path else name

                if isinstance(content, list):
                    # 创建目录和文件列表
                    dir_is_safe, dir_abs_path, dir_error = SecurityValidator.validate_path(current_path)
                    if dir_is_safe:
                        os.makedirs(dir_abs_path, exist_ok=True)
                        created_dirs.append(current_path)

                        # 创建文件
                        for filename in content:
                            file_path = f"{current_path}/{filename}"
                            file_is_safe, file_abs_path, file_error = SecurityValidator.validate_path(file_path)
                            if file_is_safe:
                                try:
                                    with open(file_abs_path, 'w') as f:
                                        f.write("")  # 创建空文件
                                    created_files.append(file_path)
                                except Exception as e:
                                    failed_operations.append({"path": file_path, "error": str(e)})
                            else:
                                failed_operations.append({"path": file_path, "error": file_error})
                    else:
                        failed_operations.append({"path": current_path, "error": dir_error})

                elif isinstance(content, dict):
                    # 递归创建子目录
                    _create_recursive(content, current_path)

        _create_recursive(structure)

        return {
            "success": True,
            "created_files": created_files,
            "created_dirs": created_dirs,
            "failed_operations": failed_operations
        }

    except Exception as e:
        return {"success": False, "error": f"项目结构创建失败: {str(e)}"}

def _validate_file_content(file_path: str, content: str, file_type: str = None) -> Dict[str, Any]:
    """验证文件内容"""
    validation = {
        "syntax_valid": True,
        "security_check": True,
        "file_type_match": True,
        "issues": []
    }

    try:
        # 基于文件类型进行验证
        if file_type == "json" or file_path.endswith(".json"):
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                validation["syntax_valid"] = False
                validation["issues"].append(f"JSON语法错误: {str(e)}")

        # 安全检查：查找潜在的恶意代码
        dangerous_patterns = [
            "eval(", "exec(", "import os", "import subprocess",
            "__import__", "open(", "system(", "popen("
        ]

        for pattern in dangerous_patterns:
            if pattern in content:
                validation["security_check"] = False
                validation["issues"].append(f"检测到潜在危险模式: {pattern}")

    except Exception as e:
        validation["issues"].append(f"验证过程出错: {str(e)}")

    return validation

def _is_text_file(content: str) -> bool:
    """判断是否为文本文件"""
    # 简单的文本文件检测
    try:
        content.encode('utf-8')
        # 检查是否包含大量二进制字符
        binary_chars = sum(1 for c in content if ord(c) < 32 and c not in '\n\r\t')
        return binary_chars / len(content) < 0.1 if content else True
    except:
        return False