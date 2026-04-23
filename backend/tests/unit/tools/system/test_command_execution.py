import pytest
import os
import subprocess
import tempfile
from unittest.mock import patch, MagicMock
from app.tools.system.command_execution import _execute_command
from app.tools.system.config import system_config

class TestCommandExecution:
    @pytest.fixture
    def temp_project_dir(self):
        """创建临时项目目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_root = system_config.project_root
            system_config.project_root = tmpdir

            yield tmpdir

            # 恢复配置
            system_config.project_root = old_root

    def test_execute_command_success(self, temp_project_dir):
        """测试成功执行命令"""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.return_value = ("output", "")
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            result = _execute_command("echo test", timeout=30)

            assert result["success"] is True
            assert result["exit_code"] == 0
            assert result["stdout"] == "output"
            assert result["stderr"] == ""

    def test_execute_command_failure(self, temp_project_dir):
        """测试命令执行失败"""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.return_value = ("", "error message")
            mock_process.returncode = 1
            mock_popen.return_value = mock_process

            result = _execute_command("invalid command", timeout=30)

            assert result["success"] is False
            assert result["exit_code"] == 1
            assert result["stderr"] == "error message"

    def test_execute_command_timeout(self, temp_project_dir):
        """测试命令超时"""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.side_effect = subprocess.TimeoutExpired("cmd", 1)
            mock_process.returncode = -1
            mock_popen.return_value = mock_process

            result = _execute_command("sleep 10", timeout=1)

            assert result["success"] is False
            assert result["timeout_reached"] is True
            assert "超时" in result["error"]

    def test_execute_command_output_size_limit(self, temp_project_dir):
        """测试命令输出大小限制"""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            # 模拟大输出
            large_output = "x" * (system_config.max_output_size + 1)
            mock_process.communicate.return_value = (large_output, "")
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            result = _execute_command("cat large_file", timeout=30)

            assert result["success"] is False
            assert "输出超出限制" in result["error"]

    def test_execute_command_project_directory(self, temp_project_dir):
        """测试在项目目录中执行命令"""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.return_value = ("", "")
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            _execute_command("ls", timeout=30)

            # 验证命令在项目目录中执行
            mock_popen.assert_called_once()
            call_kwargs = mock_popen.call_args[1]
            assert call_kwargs["cwd"] == temp_project_dir

    def test_execute_command_duration_tracking(self, temp_project_dir):
        """测试命令执行时间跟踪"""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.return_value = ("", "")
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            result = _execute_command("echo test", timeout=30)

            assert "duration" in result
            assert isinstance(result["duration"], float)
            assert result["duration"] >= 0

    def test_execute_command_exception_handling(self, temp_project_dir):
        """测试命令执行异常处理"""
        with patch('subprocess.Popen') as mock_popen:
            mock_popen.side_effect = Exception("执行异常")

            result = _execute_command("test command", timeout=30)

            assert result["success"] is False
            assert "执行异常" in result["error"]

    def test_execute_command_with_stderr(self, temp_project_dir):
        """测试命令执行错误输出"""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.return_value = ("", "error output")
            mock_process.returncode = 1
            mock_popen.return_value = mock_process

            result = _execute_command("failing command", timeout=30)

            assert result["success"] is False
            assert result["exit_code"] == 1
            assert result["stderr"] == "error output"

    def test_execute_command_successful_exit_codes(self, temp_project_dir):
        """测试成功退出码"""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.return_value = ("success", "")
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            result = _execute_command("successful command", timeout=30)

            assert result["success"] is True
            assert result["exit_code"] == 0

    def test_execute_command_info_structure(self, temp_project_dir):
        """测试命令执行结果结构"""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.return_value = ("output", "error")
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            result = _execute_command("test command", timeout=30)

            # 验证结果包含所有必要字段
            required_fields = ["success", "command", "exit_code", "stdout", "stderr", "duration"]
            for field in required_fields:
                assert field in result, f"结果缺少字段: {field}"

            assert result["command"] == "test command"
            assert result["stdout"] == "output"
            assert result["stderr"] == "error"