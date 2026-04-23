import pytest
import os
import tempfile
import json
from datetime import datetime
from unittest.mock import patch
from app.tools.system.project_monitor import get_project_status, list_project_files, analyze_project_structure, monitor_file_changes, get_project_statistics
from app.tools.system.config import system_config

class TestProjectMonitor:
    @pytest.fixture
    def temp_project_dir(self):
        """创建临时项目目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_root = system_config.project_root
            system_config.project_root = tmpdir

            # 创建测试项目结构
            self._create_test_project_structure(tmpdir)

            yield tmpdir

            # 恢复配置
            system_config.project_root = old_root

    def _create_test_project_structure(self, base_dir):
        """创建测试项目结构"""
        # 创建目录
        os.makedirs(os.path.join(base_dir, "src", "components"), exist_ok=True)
        os.makedirs(os.path.join(base_dir, "public"), exist_ok=True)

        # 创建文件
        test_files = [
            ("package.json", '{"name": "test-project", "version": "1.0.0"}'),
            ("README.md", "# Test Project\nThis is a test project."),
            ("src/index.js", "console.log('Hello World');")
        ]

        for file_path, content in test_files:
            full_path = os.path.join(base_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)

    def test_get_project_status_directory(self, temp_project_dir):
        """测试获取项目目录状态"""
        result = get_project_status.invoke({"project_path": "."})
        print(f"Debug: result = {result}")  # 添加调试信息

        assert result["success"] is True
        assert result["is_directory"] is True
        assert "directory_info" in result
        assert result["directory_info"]["total_items"] > 0

    def test_get_project_status_file(self, temp_project_dir):
        """测试获取项目文件状态"""
        result = get_project_status.invoke({"project_path": "package.json"})

        assert result["success"] is True
        assert result["is_directory"] is False
        assert "file_info" in result
        assert result["file_info"]["extension"] == ".json"

    def test_get_project_status_invalid_path(self, temp_project_dir):
        """测试获取无效路径状态"""
        result = get_project_status.invoke({"project_path": "../../../etc/passwd"})

        assert result["success"] is False
        assert "路径超出项目目录范围" in result["error"]

    def test_list_project_files_recursive(self, temp_project_dir):
        """测试递归列出项目文件"""
        result = list_project_files.invoke({
            "directory": ".",
            "recursive": True
        })

        assert result["success"] is True
        assert result["total_files"] > 0
        assert result["total_directories"] > 0
        assert len(result["files"]) > 0
        assert len(result["directories"]) > 0

    def test_list_project_files_non_recursive(self, temp_project_dir):
        """测试非递归列出项目文件"""
        result = list_project_files.invoke({
            "directory": ".",
            "recursive": False
        })

        assert result["success"] is True
        # 非递归应该只有根目录的文件
        assert "src" in [d["name"] for d in result["directories"]]

    def test_list_project_files_with_filter(self, temp_project_dir):
        """测试按文件类型过滤"""
        result = list_project_files.invoke({
            "directory": ".",
            "recursive": True,
            "file_types": [".json", ".md"]
        })

        assert result["success"] is True
        # 应该只包含.json和.md文件
        for file_info in result["files"]:
            assert file_info["extension"] in [".json", ".md"]

    def test_analyze_project_structure(self, temp_project_dir):
        """测试分析项目结构"""
        result = analyze_project_structure.invoke({"root_directory": "."})

        assert result["success"] is True
        assert "structure" in result
        assert "summary" in result
        assert "recommendations" in result
        assert result["summary"]["total_files"] > 0

    def test_monitor_file_changes_no_change(self, temp_project_dir):
        """测试文件无变化监控"""
        # 先获取当前修改时间
        file_path = "package.json"
        abs_path = os.path.join(temp_project_dir, file_path)
        current_mtime = os.path.getmtime(abs_path)
        last_modified = datetime.fromtimestamp(current_mtime).isoformat()

        result = monitor_file_changes.invoke({
            "file_path": file_path,
            "last_modified": last_modified
        })

        assert result["success"] is True
        assert result["change_detected"] is False

    def test_monitor_file_changes_with_change(self, temp_project_dir):
        """测试文件有变化监控"""
        file_path = "package.json"

        # 使用过去的修改时间
        past_time = "2020-01-01T00:00:00"

        result = monitor_file_changes.invoke({
            "file_path": file_path,
            "last_modified": past_time
        })

        assert result["success"] is True
        assert result["change_detected"] is True

    def test_get_project_statistics(self, temp_project_dir):
        """测试获取项目统计信息"""
        result = get_project_statistics.invoke({"directory": "."})

        assert result["success"] is True
        assert "total_stats" in result
        assert "file_type_stats" in result
        assert "size_analysis" in result
        assert result["total_stats"]["total_files"] > 0

    def test_project_structure_analysis_depth(self, temp_project_dir):
        """测试项目结构分析深度"""
        result = analyze_project_structure.invoke({"root_directory": "."})

        assert result["success"] is True
        assert "structure" in result
        # 检查是否包含子目录结构
        structure = result["structure"]
        assert "src" in structure
        if "src" in structure and "contents" in structure["src"]:
            assert "components" in structure["src"]["contents"]

    def test_file_type_analysis(self, temp_project_dir):
        """测试文件类型分析"""
        result = get_project_statistics.invoke({"directory": "."})

        assert result["success"] is True
        file_types = result["file_type_stats"]
        assert ".json" in file_types
        assert ".md" in file_types
        assert file_types[".json"]["count"] >= 1

    def test_directory_size_analysis(self, temp_project_dir):
        """测试目录大小分析"""
        result = get_project_statistics.invoke({"directory": "."})

        assert result["success"] is True
        size_analysis = result["size_analysis"]
        assert "directory_sizes" in size_analysis
        assert "total_directories_with_files" in size_analysis

    def test_project_recommendations(self, temp_project_dir):
        """测试项目建议生成"""
        result = analyze_project_structure.invoke({"root_directory": "."})

        assert result["success"] is True
        recommendations = result["recommendations"]
        assert isinstance(recommendations, list)

    def test_empty_directory_analysis(self, temp_project_dir):
        """测试空目录分析"""
        # 创建空目录
        empty_dir = os.path.join(temp_project_dir, "empty")
        os.makedirs(empty_dir, exist_ok=True)

        result = get_project_statistics.invoke({"directory": "empty"})

        assert result["success"] is True
        assert result["total_stats"]["total_files"] == 0
        assert result["total_stats"]["total_size"] == 0

    def test_nonexistent_path(self, temp_project_dir):
        """测试不存在的路径"""
        result = get_project_status.invoke({"project_path": "nonexistent"})

        assert result["success"] is False
        assert "路径不存在" in result["error"]

    def test_file_monitoring_nonexistent_file(self, temp_project_dir):
        """测试监控不存在的文件"""
        result = monitor_file_changes.invoke({"file_path": "nonexistent.txt"})

        assert result["success"] is False
        assert "文件不存在" in result["error"]