"""
V2 Tool 配置

定义项目根目录、安全限制、命令白名单等配置。
"""

import os
from pathlib import Path

# ========== 项目根目录配置 ==========

# 生成的项目存放目录（按 session_id 隔离）
PROJECTS_ROOT = Path(os.environ.get("PAGEFORGE_PROJECTS_ROOT", "./generated_projects"))
GENERATED_PROJECTS_DIR = PROJECTS_ROOT / "sessions"

# 确保目录存在
GENERATED_PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


# ========== 安全限制配置 ==========

# 文件大小限制（防止写入过大文件）
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB

# 读取文件大小限制
MAX_READ_SIZE = 512 * 1024  # 512KB

# 命令执行超时（秒）
COMMAND_TIMEOUT = 30

# 命令输出大小限制（防止输出撑爆上下文）
MAX_OUTPUT_SIZE = 100 * 1024  # 100KB


# ========== 命令白名单（P0 阶段） ==========

ALLOWED_COMMANDS = frozenset({
    # Node.js 生态
    "npm", "npx", "node",

    # 文件操作（只读类）
    "ls", "cat", "head", "tail", "wc", "find",

    # 版本控制
    "git",
})


# ========== 危险命令模式黑名单 ==========

DANGEROUS_PATTERNS = [
    "rm -rf /",  # 删根
    "sudo", "su", "ssh", "scp",  # 提权/远程
    "chmod 777", "mkfs", "dd if=",  # 权限/磁盘操作
    "| sh", "| bash", "; bash", "&& bash",  # 管道注入
    "curl | sh", "wget | sh",  # 远程注入
]


# ========== 忽略的目录和文件（list_files 时跳过） ==========

IGNORED_PATTERNS = [
    "node_modules",
    ".git",
    "__pycache__",
    ".DS_Store",
    "dist",
    "build",
    ".next",
    ".nuxt",
]
