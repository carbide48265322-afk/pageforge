"""
V2 Tool 安全校验器

提供路径校验、命令校验等安全机制。
"""

import os
import re
from pathlib import Path
from typing import Tuple
from .config import (
    GENERATED_PROJECTS_DIR,
    MAX_FILE_SIZE,
    MAX_READ_SIZE,
    ALLOWED_COMMANDS,
    DANGEROUS_PATTERNS,
)


class SecurityValidator:
    """安全校验器"""

    @staticmethod
    def validate_session_id(session_id: str) -> Tuple[bool, str]:
        """
        校验 session_id 是否合法

        Returns:
            (is_valid, error_message)
        """
        if not session_id or not isinstance(session_id, str):
            return False, "session_id 不能为空"

        # 只允许字母、数字、下划线、短横线
        if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
            return False, "session_id 格式不合法"

        return True, ""

    @staticmethod
    def get_session_dir(session_id: str) -> Path:
        """获取 session 对应的项目目录"""
        return GENERATED_PROJECTS_DIR / session_id

    @staticmethod
    def validate_path(path: str, session_id: str) -> Tuple[bool, Path, str]:
        """
        校验路径安全性，返回绝对路径

        Args:
            path: 相对路径（如 "src/App.tsx"）
            session_id: 会话 ID

        Returns:
            (is_safe, absolute_path, error_message)
        """
        # 校验 session_id
        is_valid, error = SecurityValidator.validate_session_id(session_id)
        if not is_valid:
            return False, Path(""), error

        # 获取 session 目录
        session_dir = SecurityValidator.get_session_dir(session_id)

        try:
            # 规范化路径（去除开头的 / 和 ../）
            clean_path = path.strip().lstrip('/')

            # 转换为绝对路径
            abs_path = (session_dir / clean_path).resolve()

            # 校验是否在 session 目录内
            try:
                abs_path.relative_to(session_dir)
            except ValueError:
                return False, Path(""), f"路径超出项目目录范围: {path}"

            return True, abs_path, ""

        except Exception as e:
            return False, Path(""), f"路径校验错误: {str(e)}"

    @staticmethod
    def validate_file_size(size: int, is_write: bool = True) -> Tuple[bool, str]:
        """
        校验文件大小

        Args:
            size: 文件大小（字节）
            is_write: 是否为写入操作（写入和读取的限制不同）

        Returns:
            (is_safe, error_message)
        """
        limit = MAX_FILE_SIZE if is_write else MAX_READ_SIZE
        if size > limit:
            return False, f"文件大小超出限制: {size} > {limit}"

        return True, ""


class CommandValidator:
    """命令校验器"""

    @staticmethod
    def validate_command(command: str) -> Tuple[bool, str]:
        """
        校验命令是否在白名单内，且不包含危险模式

        Args:
            command: 完整命令字符串

        Returns:
            (is_safe, error_message)
        """
        if not command or not command.strip():
            return False, "命令不能为空"

        cmd = command.strip().lower()

        # 提取主命令（第一个单词）
        main_cmd = cmd.split()[0]

        # 校验白名单
        if main_cmd not in ALLOWED_COMMANDS:
            return False, f"命令 '{main_cmd}' 不在允许列表中"

        # 校验危险模式
        for pattern in DANGEROUS_PATTERNS:
            if pattern.lower() in cmd:
                return False, f"检测到危险命令模式: {pattern}"

        return True, ""

    @staticmethod
    def sanitize_args(args: list) -> Tuple[bool, list, str]:
        """
        清理命令参数（移除潜在危险字符）

        Args:
            args: 原始参数列表

        Returns:
            (is_safe, sanitized_args, error_message)
        """
        if not args:
            return True, [], ""

        sanitized = []
        for arg in args:
            # 移除管道、重定向、命令替换等危险字符
            clean_arg = re.sub(r'[;&|`$(){}<>]', '', str(arg))
            sanitized.append(clean_arg)

        return True, sanitized, ""
