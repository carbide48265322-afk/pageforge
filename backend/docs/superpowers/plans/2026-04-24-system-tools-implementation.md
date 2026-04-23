# 系统工具实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现安全的系统工具集，包括文件操作、命令执行和项目监控功能，支持大模型生成代码的安全管理和前端开发工作流

**Architecture:** 分层安全架构，包含安全验证层、工具实现层和沙箱执行层，确保文件操作和命令执行在隔离环境中安全进行

**Tech Stack:** Python + LangChain Tools + 安全验证 + 沙箱执行

---

## 📁 文件结构规划

**核心工具文件:**
- `backend/app/tools/system/file_operations.py` - 文件操作工具
- `backend/app/tools/system/command_execution.py` - 命令执行工具  
- `backend/app/tools/system/project_monitor.py` - 项目监控工具
- `backend/app/tools/system/security.py` - 安全验证组件
- `backend/app/tools/system/status_feedback.py` - 状态反馈组件

**测试文件:**
- `tests/unit/tools/system/test_file_operations.py`
- `tests/unit/tools/system/test_command_execution.py`
- `tests/unit/tools/system/test_security.py`

**配置文件:**
- `backend/app/tools/system/config.py` - 系统工具配置

---

## 🛠️ 实施任务

### Task 1: 安全验证基础组件

**Files:**
- Create: `backend/app/tools/system/security.py`
- Create: `backend/app/tools/system/config.py`
- Test: `tests/unit/tools/system/test_security.py`

- [ ] **Step 1: 创建系统工具配置文件**

```python
# backend/app/tools/system/config.py
import os
from dataclasses import dataclass

@dataclass
class SystemToolsConfig:
    """系统工具配置"""
    project_root: str = "/home/project"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    command_timeout: int = 30
    max_output_size: int = 1024 * 1024  # 1MB
    
    # 允许的命令白名单
    allowed_commands: set = frozenset([
        "npm", "node", "ls", "cat", "head", "tail", 
        "grep", "find", "wc", "cp", "mv", "mkdir", 
        "rmdir", "touch", "rm", "ps", "df", "du"
    ])
    
    # 危险命令模式
    dangerous_patterns: list = [
        "rm -rf /", "sudo", "su", "ssh", "scp",
        "> /dev", "| bash", "; bash", "&& bash",
        "chmod 777", "mkfs", "dd if=", "/dev/sd"
    ]

# 全局配置实例
system_config = SystemToolsConfig()
```

- [ ] **Step 2: 创建安全验证器**

```python
# backend/app/tools/system/security.py
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
```

- [ ] **Step 3: 编写安全验证测试**

```python
# tests/unit/tools/system/test_security.py
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
        assert "危险的路径遍历" in error
        
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
        assert "危险字符" in error
```

- [ ] **Step 4: 运行安全验证测试**

```bash
pytest tests/unit/tools/system/test_security.py -v
```

Expected: All tests pass

- [ ] **Step 5: 提交安全验证组件**

```bash
git add backend/app/tools/system/security.py backend/app/tools/system/config.py tests/unit/tools/system/test_security.py
git commit -m "feat: 添加安全验证基础组件"
```

### Task 2: 文件操作工具实现

**Files:**
- Create: `backend/app/tools/system/file_operations.py`
- Test: `tests/unit/tools/system/test_file_operations.py`

- [ ] **Step 1: 创建文件操作工具**

```python
# backend/app/tools/system/file_operations.py
import os
import shutil
import json
from datetime import datetime
from typing import Dict, List, Any
from langchain_core.tools import tool
from .security import SecurityValidator
from .config import system_config

@tool
def save_generated_code(file_path: str, code_content: str, file_type: str = None) -> Dict[str, Any]:
    """
    保存大模型生成的代码文件
    
    Args:
        file_path: 相对路径 (如: "src/components/Header.js")
        code_content: 生成的代码内容
        file_type: 文件类型 (html/css/js/json)
    
    Returns:
        操作结果
    """
    try:
        # 1. 路径安全验证
        is_safe, abs_path, error = SecurityValidator.validate_path(file_path)
        if not is_safe:
            return {"success": False, "error": error}
        
        # 2. 文件大小验证
        is_safe, error = SecurityValidator.validate_file_size(abs_path, code_content)
        if not is_safe:
            return {"success": False, "error": error}
        
        # 3. 创建父目录
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        
        # 4. 备份现有文件
        backup_path = None
        if os.path.exists(abs_path):
            backup_path = f"{abs_path}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
            shutil.copy2(abs_path, backup_path)
        
        # 5. 写入文件
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(code_content)
        
        # 6. 基础验证
        validation = _validate_file_content(abs_path, code_content, file_type)
        
        return {
            "success": True,
            "saved_path": file_path,
            "absolute_path": abs_path,
            "file_size": len(code_content),
            "backup_created": backup_path is not None,
            "backup_path": backup_path,
            "validation": validation
        }
        
    except Exception as e:
        return {"success": False, "error": f"文件保存失败: {str(e)}"}

@tool
def read_project_file(file_path: str, max_size: int = 512000) -> Dict[str, Any]:
    """
    读取项目文件内容
    
    Args:
        file_path: 文件相对路径
        max_size: 最大读取大小限制
    """
    try:
        # 1. 路径安全验证
        is_safe, abs_path, error = SecurityValidator.validate_path(file_path)
        if not is_safe:
            return {"success": False, "error": error}
        
        # 2. 检查文件是否存在
        if not os.path.exists(abs_path):
            return {"success": False, "error": f"文件不存在: {file_path}"}
        
        # 3. 检查文件大小
        file_size = os.path.getsize(abs_path)
        if file_size > max_size:
            return {"success": False, "error": f"文件过大: {file_size} > {max_size}"}
        
        # 4. 读取文件内容
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "success": True,
            "content": content,
            "encoding": "utf-8",
            "size": file_size,
            "last_modified": datetime.fromtimestamp(os.path.getmtime(abs_path)).isoformat(),
            "is_text_file": _is_text_file(content)
        }
        
    except Exception as e:
        return {"success": False, "error": f"文件读取失败: {str(e)}"}

@tool
def create_project_structure(structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    创建项目文件结构
    
    Args:
        structure: 项目结构定义
    """
    try:
        created_files = []
        created_dirs = []
        failed_operations = []
        
        def _create_recursive(current_structure, base_path=""):
            for name, content in current_structure.items():
                current_path = f"{base_path}/{name}" if base_path else name
                
                if isinstance(content, list):
                    # 创建目录和文件列表
                    dir_is_safe, dir_abs_path, dir_error = SecurityValidator.validate_path(current_path)
                    if dir_is_safe:
                        os.makedirs(dir_abs_path, exist_ok=True)
                        created_dirs.append(current_path)
                        
                        # 创建文件
                        for filename in content:
                            file_path = f"{current_path}/{filename}"
                            file_is_safe, file_abs_path, file_error = SecurityValidator.validate_path(file_path)
                            if file_is_safe:
                                try:
                                    with open(file_abs_path, 'w') as f:
                                        f.write("")  # 创建空文件
                                    created_files.append(file_path)
                                except Exception as e:
                                    failed_operations.append({"path": file_path, "error": str(e)})
                            else:
                                failed_operations.append({"path": file_path, "error": file_error})
                    else:
                        failed_operations.append({"path": current_path, "error": dir_error})
                        
                elif isinstance(content, dict):
                    # 递归创建子目录
                    _create_recursive(content, current_path)
        
        _create_recursive(structure)
        
        return {
            "success": True,
            "created_files": created_files,
            "created_dirs": created_dirs,
            "failed_operations": failed_operations
        }
        
    except Exception as e:
        return {"success": False, "error": f"项目结构创建失败: {str(e)}"}

def _validate_file_content(file_path: str, content: str, file_type: str = None) -> Dict[str, Any]:
    """验证文件内容"""
    validation = {
        "syntax_valid": True,
        "security_check": True,
        "file_type_match": True,
        "issues": []
    }
    
    try:
        # 基于文件类型进行验证
        if file_type == "json" or file_path.endswith(".json"):
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                validation["syntax_valid"] = False
                validation["issues"].append(f"JSON语法错误: {str(e)}")
        
        # 安全检查：查找潜在的恶意代码
        dangerous_patterns = [
            "eval(", "exec(", "import os", "import subprocess",
            "__import__", "open(", "system(", "popen("
        ]
        
        for pattern in dangerous_patterns:
            if pattern in content:
                validation["security_check"] = False
                validation["issues"].append(f"检测到潜在危险模式: {pattern}")
        
    except Exception as e:
        validation["issues"].append(f"验证过程出错: {str(e)}")
    
    return validation

def _is_text_file(content: str) -> bool:
    """判断是否为文本文件"""
    # 简单的文本文件检测
    try:
        content.encode('utf-8')
        # 检查是否包含大量二进制字符
        binary_chars = sum(1 for c in content if ord(c) < 32 and c not in '\n\r\t')
        return binary_chars / len(content) < 0.1 if content else True
    except:
        return False
```

- [ ] **Step 2: 编写文件操作测试**

```python
# tests/unit/tools/system/test_file_operations.py
import pytest
import os
import tempfile
from app.tools.system.file_operations import save_generated_code, read_project_file, create_project_structure

class TestFileOperations:
    @pytest.fixture
    def temp_project_dir(self):
        """创建临时项目目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_root = "/home/project"
            # 临时修改配置用于测试
            import app.tools.system.config as config
            config.system_config.project_root = tmpdir
            
            yield tmpdir
            
            # 恢复配置
            config.system_config.project_root = old_root
    
    def test_save_generated_code(self, temp_project_dir):
        """测试保存代码文件"""
        result = save_generated_code("src/test.js", "console.log('hello world');", "javascript")
        
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
        
        result = read_project_file("test.txt")
        
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
        
        result = create_project_structure(structure)
        
        assert result["success"] is True
        assert len(result["created_dirs"]) >= 2
        assert len(result["created_files"]) >= 3
        assert "src" in str(result["created_dirs"])
        assert "public" in str(result["created_dirs"])
    
    def test_security_validation(self, temp_project_dir):
        """测试安全验证"""
        # 测试危险路径
        result = save_generated_code("../../../etc/passwd", "malicious content")
        assert result["success"] is False
        assert "危险的路径遍历" in result["error"]
        
        # 测试文件过大
        large_content = "x" * (10 * 1024 * 1024 + 1)  # 超过10MB
        result = save_generated_code("large.txt", large_content)
        assert result["success"] is False
        assert "文件大小超出限制" in result["error"]
```

- [ ] **Step 3: 运行文件操作测试**

```bash
pytest tests/unit/tools/system/test_file_operations.py -v
```

Expected: All tests pass

- [ ] **Step 4: 提交文件操作工具**

```bash
git add backend/app/tools/system/file_operations.py tests/unit/tools/system/test_file_operations.py
git commit -m "feat: 添加文件操作工具"
```

### Task 3: 命令执行工具实现

**Files:**
- Create: `backend/app/tools/system/command_execution.py`
- Test: `tests/unit/tools/system/test_command_execution.py`

- [ ] **Step 1: 创建命令执行工具**

```python
# backend/app/tools/system/command_execution.py
import subprocess
import json
import time
from typing import Dict, List, Any, Optional
from langchain_core.tools import tool
from .security import CommandValidator, SecurityValidator
from .config import system_config

@tool
def execute_npm_command(command: str, args: List[str] = None, timeout: int = 120) -> Dict[str, Any]:
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

@tool
def execute_node_command(script_path: str, args: List[str] = None, timeout: int = 60) -> Dict[str, Any]:
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
                return {"success": False