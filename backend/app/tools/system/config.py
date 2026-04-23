import os
from dataclasses import dataclass, field

@dataclass
class SystemToolsConfig:
    """系统工具配置"""
    project_root: str = "/home/project"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    command_timeout: int = 30
    max_output_size: int = 1024 * 1024  # 1MB

    # 允许的命令白名单
    allowed_commands: frozenset = field(default_factory=lambda: frozenset([
        "npm", "node", "ls", "cat", "head", "tail",
        "grep", "find", "wc", "cp", "mv", "mkdir",
        "rmdir", "touch", "rm", "ps", "df", "du"
    ]))

    # 危险命令模式
    dangerous_patterns: list = field(default_factory=lambda: [
        "rm -rf /", "sudo", "su", "ssh", "scp",
        "> /dev", "| bash", "; bash", "&& bash",
        "chmod 777", "mkfs", "dd if=", "/dev/sd"
    ])

# 全局配置实例
system_config = SystemToolsConfig()