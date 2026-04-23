import subprocess
import json
import time
import os
from typing import Dict, List, Any, Optional
from langchain_core.tools import tool
from .security import CommandValidator, SecurityValidator
from .config import system_config
from app.core import registry

@registry.register_tool
@tool
def execute_npm_command(command: str, args: Optional[List[str]] = None, timeout: int = 120) -> Dict[str, Any]:
    """
    安全执行npm相关命令

    Args:
        command: npm命令 (install/lint/test/build/dev)
        args: 命令参数
        timeout: 执行超时时间
    """
    try:
        # 构建完整命令
        cmd_parts = ["npm"]

        command_mapping = {
            "install": "install",
            "lint": ["run", "lint"],
            "test": ["run", "test"],
            "build": ["run", "build"],
            "dev": ["run", "dev"]
        }

        if command not in command_mapping:
            return {"success": False, "error": f"不支持的npm命令: {command}"}

        cmd_parts.extend(command_mapping[command] if isinstance(command_mapping[command], list) else [command_mapping[command]])

        if args:
            is_safe, sanitized_args, error = CommandValidator.sanitize_command_args(args)
            if not is_safe:
                return {"success": False, "error": error}
            cmd_parts.extend(sanitized_args)

        full_command = " ".join(cmd_parts)

        # 验证命令安全性
        is_safe, error = CommandValidator.validate_command(full_command)
        if not is_safe:
            return {"success": False, "error": error}

        # 执行命令
        return _execute_command(full_command, timeout)

    except Exception as e:
        return {"success": False, "error": f"npm命令执行失败: {str(e)}"}

@registry.register_tool
@tool
def execute_node_command(script_path: str, args: Optional[List[str]] = None, timeout: int = 60) -> Dict[str, Any]:
    """
    执行Node.js脚本

    Args:
        script_path: 脚本文件路径
        args: 脚本参数
        timeout: 执行超时时间
    """
    try:
        # 验证脚本路径
        is_safe, abs_path, error = SecurityValidator.validate_path(script_path)
        if not is_safe:
            return {"success": False, "error": error}

        if not os.path.exists(abs_path):
            return {"success": False, "error": f"脚本文件不存在: {script_path}"}

        # 构建命令
        cmd_parts = ["node", script_path]

        if args:
            is_safe, sanitized_args, error = CommandValidator.sanitize_command_args(args)
            if not is_safe:
                return {"success": False, "error": error}
            cmd_parts.extend(sanitized_args)

        full_command = " ".join(cmd_parts)

        # 验证命令安全性
        is_safe, error = CommandValidator.validate_command(full_command)
        if not is_safe:
            return {"success": False, "error": error}

        # 执行命令
        return _execute_command(full_command, timeout)

    except Exception as e:
        return {"success": False, "error": f"Node命令执行失败: {str(e)}"}

@registry.register_tool
@tool
def execute_shell_command(command: str, args: Optional[List[str]] = None, timeout: int = 30) -> Dict[str, Any]:
    """
    执行通用shell命令（受限）

    Args:
        command: 命令名称
        args: 命令参数
        timeout: 执行超时时间
    """
    try:
        # 构建完整命令
        cmd_parts = [command]

        if args:
            is_safe, sanitized_args, error = CommandValidator.sanitize_command_args(args)
            if not is_safe:
                return {"success": False, "error": error}
            cmd_parts.extend(sanitized_args)

        full_command = " ".join(cmd_parts)

        # 验证命令安全性
        is_safe, error = CommandValidator.validate_command(full_command)
        if not is_safe:
            return {"success": False, "error": error}

        # 执行命令
        return _execute_command(full_command, timeout)

    except Exception as e:
        return {"success": False, "error": f"Shell命令执行失败: {str(e)}"}

def _execute_command(command: str, timeout: int = 30) -> Dict[str, Any]:
    """
    执行命令的内部函数

    Args:
        command: 完整命令字符串
        timeout: 超时时间

    Returns:
        执行结果
    """
    start_time = time.time()
    result = {
        "success": False,
        "command": command,
        "exit_code": None,
        "stdout": "",
        "stderr": "",
        "duration": 0,
        "timeout_reached": False
    }

    try:
        # 在项目目录中执行命令
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=system_config.project_root
        )

        try:
            stdout, stderr = process.communicate(timeout=timeout)
            result["exit_code"] = process.returncode
            result["stdout"] = stdout
            result["stderr"] = stderr

            # 检查输出大小限制
            output_size = len(stdout) + len(stderr)
            if output_size > system_config.max_output_size:
                return {
                    "success": False,
                    "error": f"命令输出超出限制: {output_size} > {system_config.max_output_size}",
                    "exit_code": result["exit_code"],
                    "output_truncated": True
                }

            result["success"] = process.returncode == 0

        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            result["timeout_reached"] = True
            result["success"] = False
            result["error"] = f"命令执行超时: {timeout}秒"

    except Exception as e:
        result["error"] = f"命令执行异常: {str(e)}"
        result["success"] = False

    finally:
        result["duration"] = time.time() - start_time

    return result

@registry.register_tool
@tool
def get_command_help(command: str) -> Dict[str, Any]:
    """
    获取命令帮助信息

    Args:
        command: 命令名称
    """
    try:
        # 验证命令是否在允许列表中
        if command not in system_config.allowed_commands:
            return {
                "success": False,
                "error": f"命令 '{command}' 不在允许列表中",
                "available_commands": list(system_config.allowed_commands)
            }

        # 执行帮助命令
        help_commands = {
            "npm": ["npm", "help"],
            "node": ["node", "--help"],
            "ls": ["ls", "--help"],
            "cat": ["cat", "--help"]
        }

        if command in help_commands:
            cmd_parts = help_commands[command]
            full_command = " ".join(cmd_parts)

            help_result = _execute_command(full_command, timeout=10)

            return {
                "success": True,
                "command": command,
                "help_info": help_result["stdout"],
                "exit_code": help_result["exit_code"]
            }
        else:
            return {
                "success": True,
                "command": command,
                "help_info": f"命令 '{command}' 的帮助信息不可用",
                "note": "请参考相关文档获取帮助"
            }

    except Exception as e:
        return {"success": False, "error": f"获取帮助信息失败: {str(e)}"}