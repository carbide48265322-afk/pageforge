import pytest
from app.tools.system.security import SecurityValidator, CommandValidator

class TestSecurityValidator:
    def test_path_validation(self):
        """测试路径验证"""
        # 有效路径
        is_safe, path, error = SecurityValidator.validate_path("src/test.js")
        assert is_safe is True
        assert "src/test.js" in path
        assert error == ""

        # 危险路径遍历
        is_safe, path, error = SecurityValidator.validate_path("../../../etc/passwd")
        assert is_safe is False
        assert "路径超出项目目录范围" in error or "危险的路径遍历" in error

        # 空路径
        is_safe, path, error = SecurityValidator.validate_path("")
        assert is_safe is False
        assert "路径不能为空" in error

    def test_file_size_validation(self):
        """测试文件大小验证"""
        # 正常大小
        is_safe, error = SecurityValidator.validate_file_size("test.txt", "small content")
        assert is_safe is True
        assert error == ""

    def test_command_validation(self):
        """测试命令验证"""
        # 安全命令
        is_safe, error = CommandValidator.validate_command("ls -la")
        assert is_safe is True
        assert error == ""

        # 危险命令
        is_safe, error = CommandValidator.validate_command("sudo rm -rf /")
        assert is_safe is False
        assert "sudo" in error

        # 危险字符
        is_safe, error = CommandValidator.validate_command("cat file.txt; rm -rf /")
        assert is_safe is False
        assert "危险字符" in error or "危险命令模式" in error

    def test_command_whitelist(self):
        """测试命令白名单"""
        # 白名单中的命令
        for cmd in ["npm install", "node --version", "ls -la", "cat file.txt"]:
            is_safe, error = CommandValidator.validate_command(cmd)
            assert is_safe is True, f"命令 '{cmd}' 应该被允许但失败了: {error}"

        # 不在白名单中的命令
        is_safe, error = CommandValidator.validate_command("curl http://example.com")
        assert is_safe is False
        assert "不在允许列表中" in error

    def test_dangerous_patterns(self):
        """测试危险模式检测"""
        dangerous_commands = [
            "rm -rf /",
            "sudo apt update",
            "ssh user@host",
            "cat file > /dev/sda",
            "echo test | bash",
            "wget url; bash",
            "chmod 777 /etc/passwd"
        ]

        for cmd in dangerous_commands:
            is_safe, error = CommandValidator.validate_command(cmd)
            assert is_safe is False, f"危险命令 '{cmd}' 应该被阻止"

    def test_sanitize_command_args(self):
        """测试命令参数清理"""
        # 正常参数
        is_safe, sanitized, error = CommandValidator.sanitize_command_args(["--version", "--help"])
        assert is_safe is True
        assert sanitized == ["--version", "--help"]
        assert error == ""

        # 包含危险字符的参数
        is_safe, sanitized, error = CommandValidator.sanitize_command_args(["file.txt; rm", "test|bash"])
        assert is_safe is True
        assert ";" not in sanitized[0]
        assert "|" not in sanitized[1]

    def test_path_edge_cases(self):
        """测试路径边界情况"""
        # 相对路径
        is_safe, path, error = SecurityValidator.validate_path("./src/test.js")
        assert is_safe is True

        # 绝对路径（应该被转换为相对路径）
        is_safe, path, error = SecurityValidator.validate_path("/home/project/src/test.js")
        assert is_safe is True
        assert path.endswith("src/test.js")

        # 包含多个../的路径
        is_safe, path, error = SecurityValidator.validate_path("../../../../etc/passwd")
        assert is_safe is False

    def test_file_size_limits(self):
        """测试文件大小限制"""
        # 创建大内容测试
        large_content = "x" * (10 * 1024 * 1024 + 1)  # 超过10MB
        is_safe, error = SecurityValidator.validate_file_size("large.txt", large_content)
        assert is_safe is False
        assert "文件大小超出限制" in error