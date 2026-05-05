"""
V2 Tool: run_command

在 session 目录下执行 shell 命令（npm/npx/node 等）。
执行时推送 tool_call:*/command_output 事件。
"""

import subprocess
import shlex
import time
from pathlib import Path
from typing import Dict, Any, Optional
from langchain_core.tools import tool
from .security import SecurityValidator, CommandValidator
from .config import COMMAND_TIMEOUT, MAX_OUTPUT_SIZE

# 尝试导入 event_emitter（如果可用）
try:
    from app.graph.event_emitter import (
        emit_tool_call_start,
        emit_tool_call_end,
        emit_command_output,
    )
    HAS_EMITTER = True
except ImportError:
    HAS_EMITTER = False


@tool
def run_command(
    command: str,
    session_id: str,
    args: Optional[list] = None,
    timeout: int = COMMAND_TIMEOUT
) -> Dict[str, Any]:
    """
    在 session 目录下执行 shell 命令

    Args:
        command: 命令名称（如 "npm"、"npx"、"node"）
        args: 命令参数列表（如 ["install", "react"]）
        session_id: 会话 ID
        timeout: 执行超时时间（秒），默认 30

    Returns:
        执行结果，包含 success、stdout、stderr、exit_code、duration 等信息
    """
    tool_id = f"run_command_{int(time.time() * 1000)}"
    start_time = time.time()

    # 推送工具开始事件
    if HAS_EMITTER:
        emit_tool_call_start(
            tool_id=tool_id,
            name="run_command",
            input={"command": command, "args": args, "session_id": session_id},
        )

    try:
        # 1. 构建完整命令
        cmd_parts = [command]

        if args:
            # 清理参数
            is_safe, sanitized_args, error = CommandValidator.sanitize_args(args)
            if not is_safe:
                if HAS_EMITTER:
                    emit_tool_call_end(tool_id, "error", error=error)
                return {"success": False, "error": error}
            cmd_parts.extend(sanitized_args)

        full_command = " ".join(shlex.quote(part) for part in cmd_parts)

        # 2. 校验命令安全性
        is_safe, error = CommandValidator.validate_command(full_command)
        if not is_safe:
            if HAS_EMITTER:
                emit_tool_call_end(tool_id, "error", error=error)
            return {"success": False, "error": error}

        # 3. 获取 session 目录作为工作目录
        session_dir = SecurityValidator.get_session_dir(session_id)
        if not session_dir.exists():
            error = f"session 目录不存在: {session_id}"
            if HAS_EMITTER:
                emit_tool_call_end(tool_id, "error", error=error)
            return {"success": False, "error": error}

        # 4. 执行命令
        result = _execute_command(
            full_command,
            cwd=str(session_dir),
            timeout=timeout,
            tool_id=tool_id,
        )

        # 添加 session_id 到结果
        result["session_id"] = session_id
        result["command"] = full_command

        return result

    except Exception as e:
        error = f"命令执行异常: {str(e)}"
        if HAS_EMITTER:
            emit_tool_call_end(tool_id, "error", error=error)
        return {
            "success": False,
            "error": error,
            "session_id": session_id,
        }


def _execute_command(
    command: str,
    cwd: str,
    timeout: int,
    tool_id: str
) -> Dict[str, Any]:
    """
    执行命令的内部函数

    Args:
        command: 完整命令字符串（已引号包裹各部分）
        cwd: 工作目录
        timeout: 超时时间（秒）
        tool_id: 工具 ID

    Returns:
        执行结果
    """
    start_time = time.time()
    result = {
        "success": False,
        "exit_code": None,
        "stdout": "",
        "stderr": "",
        "duration": 0,
        "timeout_reached": False,
        "output_truncated": False,
    }

    try:
        # 执行命令
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd,
        )

        try:
            stdout, stderr = process.communicate(timeout=timeout)

            result["exit_code"] = process.returncode
            result["stdout"] = stdout
            result["stderr"] = stderr

            # 推送命令输出（完整输出，实际应改为实时推送）
            if HAS_EMITTER and stdout:
                emit_command_output(stdout)
                if stderr:
                    # stderr 也通过 command_output 推送
                    emit_command_output(f"[stderr] {stderr}")

            # 检查输出大小限制
            output_size = len(stdout) + len(stderr)
            if output_size > MAX_OUTPUT_SIZE:
                # 截断输出
                result["stdout"] = stdout[:MAX_OUTPUT_SIZE // 2]
                result["stderr"] = stderr[:MAX_OUTPUT_SIZE // 2]
                result["output_truncated"] = True
                result["success"] = False
                result["error"] = f"命令输出超出限制: {output_size} > {MAX_OUTPUT_SIZE}"
            else:
                result["success"] = process.returncode == 0

        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            result["timeout_reached"] = True
            result["success"] = False
            result["error"] = f"命令执行超时: {timeout}秒"

    except Exception as e:
        result["error"] = f"命令执行失败: {str(e)}"
        result["success"] = False

    finally:
        result["duration"] = round(time.time() - start_time, 2)

        # 推送工具结束事件
        if HAS_EMITTER:
            emit_tool_call_end(
                tool_id=tool_id,
                status="success" if result["success"] else "error",
                duration_ms=int(result["duration"] * 1000),
                error=result.get("error"),
            )

    return result
