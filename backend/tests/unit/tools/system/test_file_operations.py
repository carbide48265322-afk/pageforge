import pytest
import os
import tempfile
from app.tools.system.file_operations import save_generated_code, read_project_file, create_project_structure
from app.tools.system.config import system_config

class TestFileOperations:
    @pytest.fixture
    def temp_project_dir(self):
        """创建临时项目目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_root = system_config.project_root
            # 临时修改配置用于测试
            system_config.project_root = tmpdir

            yield tmpdir

            # 恢复配置
            system_config.project_root = old_root

    def test_save_generated_code(self, temp_project_dir):
        """测试保存代码文件"""
        result = save_generated_code.invoke({"file_path": "src/test.js", "code_content": "console.log('hello world');", "file_type": "javascript"})

        assert result["success"] is True
        assert result["file_size"] == len("console.log('hello world');")
        assert "src/test.js" in result["saved_path"]

        # 验证文件确实被创建
        expected_path = os.path.join(temp_project_dir, "src", "test.js")
        assert os.path.exists(expected_path)

    def test_read_project_file(self, temp_project_dir):
        """测试读取项目文件"""
        # 先创建一个文件
        test_content = "Hello, World!"
        test_path = os.path.join(temp_project_dir, "test.txt")
        with open(test_path, 'w') as f:
            f.write(test_content)

        result = read_project_file.invoke({"file_path": "test.txt"})

        assert result["success"] is True
        assert result["content"] == test_content
        assert result["size"] == len(test_content)
        assert result["is_text_file"] is True

    def test_create_project_structure(self, temp_project_dir):
        """测试创建项目结构"""
        structure = {
            "src": {
                "components": ["Header.js", "Footer.js"],
                "styles": ["main.css"]
            },
            "public": ["index.html"]
        }

        result = create_project_structure.invoke({"structure": structure})

        assert result["success"] is True
        assert len(result["created_dirs"]) >= 2
        assert len(result["created_files"]) >= 3
        assert "src" in str(result["created_dirs"])
        assert "public" in str(result["created_dirs"])

    def test_security_validation(self, temp_project_dir):
        """测试安全验证"""
        # 测试危险路径
        result = save_generated_code.invoke({"file_path": "../../../etc/passwd", "code_content": "malicious content"})
        assert result["success"] is False
        assert "路径超出项目目录范围" in result["error"]

        # 测试文件过大
        large_content = "x" * (10 * 1024 * 1024 + 1)  # 超过10MB
        result = save_generated_code.invoke({"file_path": "large.txt", "code_content": large_content})
        assert result["success"] is False
        assert "文件大小超出限制" in result["error"]

    def test_file_backup(self, temp_project_dir):
        """测试文件备份功能"""
        # 先保存一个文件
        file_path = "test.js"
        content1 = "console.log('version 1');"
        result1 = save_generated_code.invoke({"file_path": file_path, "code_content": content1})
        assert result1["success"] is True
        assert result1["backup_created"] is False  # 首次保存，无备份

        # 再次保存同一个文件
        content2 = "console.log('version 2');"
        result2 = save_generated_code.invoke({"file_path": file_path, "code_content": content2})
        assert result2["success"] is True
        assert result2["backup_created"] is True  # 应该创建备份
        assert result2["backup_path"] is not None

        # 验证备份文件存在
        assert os.path.exists(result2["backup_path"])

        # 验证新内容
        read_result = read_project_file.invoke({"file_path": file_path})
        assert read_result["success"] is True
        assert read_result["content"] == content2

    def test_json_validation(self, temp_project_dir):
        """测试JSON文件验证"""
        # 有效的JSON
        valid_json = '{"name": "test", "version": "1.0"}'
        result = save_generated_code.invoke({"file_path": "package.json", "code_content": valid_json, "file_type": "json"})
        assert result["success"] is True
        assert result["validation"]["syntax_valid"] is True

        # 无效的JSON
        invalid_json = '{"name": "test", "version":}'  # 语法错误
        result = save_generated_code.invoke({"file_path": "invalid.json", "code_content": invalid_json, "file_type": "json"})
        assert result["success"] is True  # 文件仍然保存成功
        assert result["validation"]["syntax_valid"] is False
        assert "JSON语法错误" in str(result["validation"]["issues"])

    def test_security_pattern_detection(self, temp_project_dir):
        """测试安全模式检测"""
        # 包含危险模式的代码
        dangerous_code = """
        import os
        os.system('rm -rf /')
        eval('dangerous code')
        """
        result = save_generated_code.invoke({"file_path": "dangerous.py", "code_content": dangerous_code})
        assert result["success"] is True  # 文件仍然保存
        assert result["validation"]["security_check"] is False
        assert any("import os" in issue for issue in result["validation"]["issues"])

    def test_file_type_detection(self, temp_project_dir):
        """测试文件类型检测"""
        # 文本文件
        text_content = "This is a text file."
        result = save_generated_code.invoke({"file_path": "text.txt", "code_content": text_content})
        assert result["success"] is True

        read_result = read_project_file.invoke({"file_path": "text.txt"})
        assert read_result["is_text_file"] is True

        # 二进制内容（模拟）
        binary_content = b'\x00\x01\x02\x03\x04\x05'.decode('latin-1')
        result = save_generated_code.invoke({"file_path": "binary.bin", "code_content": binary_content})
        assert result["success"] is True

        read_result = read_project_file.invoke({"file_path": "binary.bin"})
        assert read_result["is_text_file"] is False

    def test_directory_creation(self, temp_project_dir):
        """测试目录创建"""
        # 测试深层目录结构
        deep_path = "src/components/ui/buttons/primary.js"
        result = save_generated_code.invoke({"file_path": deep_path, "code_content": "// Primary button component"})
        assert result["success"] is True

        # 验证所有父目录都被创建
        expected_path = os.path.join(temp_project_dir, deep_path)
        assert os.path.exists(expected_path)
        assert os.path.exists(os.path.dirname(expected_path))

    def test_empty_project_structure(self, temp_project_dir):
        """测试空项目结构"""
        result = create_project_structure.invoke({"structure": {}})
        assert result["success"] is True
        assert result["created_files"] == []
        assert result["created_dirs"] == []
        assert result["failed_operations"] == []