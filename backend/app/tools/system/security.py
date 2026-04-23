import os
import re
from pathlib import Path
from typing import Tuple
from .config import system_config

class SecurityValidator:
    """安全验证器"""

    @classmethod
    def validate_path(cls, path: str) -> Tuple[bool, str, str]:
        """
        验证路径安全性

        Returns:
            (is_safe, normalized_path, error_message)
        """
        try:
            # 处理空路径
            if not path or not path.strip():
                return False, "", "路径不能为空"

            # 规范化路径
            clean_path = path.strip().lstrip('/')
            abs_path = os.path.abspath(os.path.join(system_config.project_root, clean_path))

            # 检查是否在项目目录内
            if not abs_path.startswith(system_config.project_root):
                return False, "", f"路径超出项目目录范围: {system_config.project_root}"

            # 检查路径遍历攻击
            rel_path = os.path.relpath(abs_path, system_config.project_root)
            if ".." in rel_path and rel_path.startswith(".."):
                return False, "", "检测到危险的路径遍历"

            return True, abs_path, ""

        except Exception as e:
            return False, "", f"路径验证错误: {str(e)}"

    @classmethod
    def validate_file_size(cls, file_path: str, content: str = None) -> Tuple[bool, str]:
        """验证文件大小"""
        try:
            if content is not None:
                size = len(content.encode('utf-8'))
            else:
                if not os.path.exists(file_path):
                    return True, ""  # 新文件无大小限制
                size = os.path.getsize(file_path)

            if size > system_config.max_file_size:
                return False, f"文件大小超出限制: {size} > {system_config.max_file_size}"

            return True, ""
        except Exception as e:
            return False, f"文件大小检查错误: {str(e)}"

class CommandValidator:
    """命令安全验证器"""

    @classmethod
    def validate_command(cls, command: str) -> Tuple[bool, str]:
        """
        验证命令安全性

        Returns:
            (is_safe, error_message)
        """
        if not command or not command.strip():
            return False, "命令不能为空"

        cmd = command.strip()
        cmd_parts = cmd.split()

        if not cmd_parts:
            return False, "空命令"

        # 检查主命令是否在白名单中
        main_cmd = cmd_parts[0]
        if main_cmd not in system_config.allowed_commands:
            return False, f"命令 '{main_cmd}' 不在允许列表中"

        # 检查危险模式
        cmd_lower = cmd.lower()
        for pattern in system_config.dangerous_patterns:
            if pattern.lower() in cmd_lower:
                return False, f"检测到危险命令模式: {pattern}"

        # 检查重定向和管道
        dangerous_chars = [">", "<", "|", ";", "&", "`", "$", "(", ")"]
        for char in dangerous_chars:
            if char in cmd and not cmd_parts[0] in ["grep", "find"]:
                # 允许某些命令使用特定符号
                return False, f"检测到危险字符: {char}"

        return True, ""

    @classmethod
    def sanitize_command_args(cls, args: list) -> Tuple[bool, list, str]:
        """清理命令参数"""
        if not args:
            return True, [], ""

        sanitized = []
        for arg in args:
            # 移除潜在的恶意字符
            clean_arg = re.sub(r'[;&|`$(){}]', '', str(arg))
            sanitized.append(clean_arg)

        return True, sanitized, ""