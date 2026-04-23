# PageForge 系统工具文档

## 概述

PageForge 系统工具是一套为 AI 驱动的代码生成和项目管理而设计的后端工具集。这些工具提供了安全的文件操作、命令执行、项目监控和状态反馈功能，确保大模型生成的代码能够安全地保存到项目目录中，并通过安全的命令执行环境进行代码质量检查。

## 架构设计

系统工具采用分层安全架构：

```
+-------------------+
|   工具接口层       | ← LangChain Tools
+-------------------+
|   业务逻辑层       | ← 文件操作、命令执行、项目监控
+-------------------+
|   安全验证层       | ← 路径验证、命令验证、大小限制
+-------------------+
|   沙箱执行层       | ← 项目目录隔离、安全执行环境
+-------------------+
```

## 核心组件

### 1. 安全验证组件 (`security.py`)

负责所有操作的安全性验证：

- **路径验证**：防止路径遍历攻击，确保操作在 `/home/project` 目录内
- **文件大小验证**：限制文件大小，防止过大文件
- **命令安全验证**：白名单机制，阻止危险命令
- **参数清理**：移除潜在的恶意字符

```python
from app.tools.system.security import SecurityValidator, CommandValidator

# 路径验证
is_safe, abs_path, error = SecurityValidator.validate_path("src/test.js")

# 命令验证
is_safe, error = CommandValidator.validate_command("npm install")
```

### 2. 文件操作工具 (`file_operations.py`)

提供安全的文件操作功能：

- **`save_generated_code`**：保存大模型生成的代码文件
- **`read_project_file`**：读取项目文件内容
- **`create_project_structure`**：创建项目文件结构

```python
# 保存生成的代码
result = save_generated_code.invoke({
    "file_path": "src/components/Header.js",
    "code_content": "import React from 'react';",
    "file_type": "javascript"
})

# 读取项目文件
result = read_project_file.invoke({"file_path": "package.json"})

# 创建项目结构
structure = {
    "src": {
        "components": ["Header.js", "Footer.js"],
        "styles": ["main.css"]
    }
}
result = create_project_structure.invoke({"structure": structure})
```

### 3. 命令执行工具 (`command_execution.py`)

提供安全的命令执行功能：

- **`execute_npm_command`**：执行 npm 相关命令
- **`execute_node_command`**：执行 Node.js 脚本
- **`execute_shell_command`**：执行通用 shell 命令
- **`get_command_help`**：获取命令帮助信息

```python
# 执行 npm 命令
result = execute_npm_command.invoke({
    "command": "install",
    "args": ["lodash"],
    "timeout": 120
})

# 执行 shell 命令
result = execute_shell_command.invoke({
    "command": "ls",
    "args": ["-la"],
    "timeout": 30
})
```

### 4. 项目监控工具 (`project_monitor.py`)

提供项目状态监控和分析功能：

- **`get_project_status`**：获取项目状态信息
- **`list_project_files`**：列出项目文件
- **`analyze_project_structure`**：分析项目结构
- **`monitor_file_changes`**：监控文件变化
- **`get_project_statistics`**：获取项目统计信息

```python
# 获取项目状态
result = get_project_status.invoke({"project_path": "."})

# 列出项目文件
result = list_project_files.invoke({
    "directory": "src",
    "recursive": True,
    "file_types": [".js", ".css"]
})

# 分析项目结构
result = analyze_project_structure.invoke({"root_directory": "."})

# 监控文件变化
result = monitor_file_changes.invoke({
    "file_path": "src/index.js",
    "last_modified": "2024-01-01T00:00:00"
})

# 获取项目统计
result = get_project_statistics.invoke({"directory": "."})
```

### 5. 状态反馈组件 (`status_feedback.py`)

提供实时状态跟踪和反馈功能：

- **`StatusFeedbackManager`**：状态管理器
- **`StatusUpdate`**：状态更新数据类
- **`with_status_feedback`**：状态反馈装饰器
- **上下文管理器函数**：快速创建操作上下文

```python
from app.tools.system.status_feedback import (
    status_manager, ProgressType, OperationStatus,
    create_file_operation_context, with_status_feedback
)

# 创建操作
op_id = status_manager.create_operation(
    "file_save_op",
    ProgressType.FILE_OPERATION,
    "保存文件"
)

# 更新进度
status_manager.update_progress(op_id, 50.0, "正在保存...")

# 完成操作
status_manager.complete_operation(op_id, "文件保存完成")

# 使用上下文管理器
ctx = create_file_operation_context("save_op", "test.js")

# 使用装饰器
@with_status_feedback(ProgressType.CODE_GENERATION, "生成代码")
def generate_code():
    # 代码生成逻辑
    return "生成的代码"
```

## 安全特性

### 路径安全验证

- ✅ 防止路径遍历攻击 (`../../../etc/passwd`)
- ✅ 限制操作在项目目录内 (`/home/project`)
- ✅ 规范化路径处理

### 命令安全验证

- ✅ 命令白名单机制
- ✅ 危险模式检测
- ✅ 参数清理和验证
- ✅ 执行超时控制

### 文件大小限制

- ✅ 最大文件大小限制 (默认 10MB)
- ✅ 命令输出大小限制 (默认 1MB)
- ✅ 自动备份机制

### 沙箱执行环境

- ✅ 项目目录隔离
- ✅ 安全的执行环境
- ✅ 错误处理和恢复

## 典型使用场景

### 场景 1：AI 生成代码保存

```python
# 1. AI 生成 React 组件代码
ai_generated_code = generate_react_component()

# 2. 使用文件操作工具保存
result = save_generated_code.invoke({
    "file_path": "src/components/GeneratedComponent.js",
    "code_content": ai_generated_code,
    "file_type": "javascript"
})

# 3. 检查保存结果
if result["success"]:
    print(f"代码保存成功: {result['saved_path']}")
    if result["validation"]["syntax_valid"]:
        print("✅ 代码语法验证通过")
    else:
        print("⚠️  代码存在语法问题")
else:
    print(f"❌ 保存失败: {result['error']}")
```

### 场景 2：代码质量检查

```python
# 1. 保存代码后执行 lint 检查
save_result = save_generated_code.invoke({
    "file_path": "src/index.js",
    "code_content": generated_code
})

if save_result["success"]:
    # 2. 执行代码质量检查
    lint_result = execute_npm_command.invoke({
        "command": "lint",
        "timeout": 60
    })

    if lint_result["success"]:
        print("✅ 代码质量检查通过")
        print(f"输出: {lint_result['stdout']}")
    else:
        print(f"❌ 代码质量问题: {lint_result['stderr']}")
```

### 场景 3：项目结构分析

```python
# 1. 分析生成的项目结构
analysis_result = analyze_project_structure.invoke({"root_directory": "."})

if analysis_result["success"]:
    summary = analysis_result["summary"]
    print(f"项目包含 {summary['total_files']} 个文件")
    print(f"项目总大小: {summary['total_size_human']}")
    print(f"文件类型分布: {summary['file_types']}")

    # 2. 获取改进建议
    for recommendation in analysis_result["recommendations"]:
        print(f"💡 建议: {recommendation}")
```

### 场景 4：实时状态反馈

```python
# 1. 创建操作上下文
ctx = create_file_operation_context("complex_operation", "multiple_files")

# 2. 模拟复杂操作
files_to_process = ["file1.js", "file2.js", "file3.js"]
total_files = len(files_to_process)

for i, file_path in enumerate(files_to_process):
    # 更新进度
    progress = (i + 1) / total_files * 100
    status_manager.update_progress(
        "complex_operation",
        progress,
        f"正在处理 {file_path}",
        {"current_file": file_path, "processed": i + 1, "total": total_files}
    )

    # 处理文件...
    time.sleep(0.1)  # 模拟处理时间

# 3. 完成操作
status_manager.complete_operation(
    "complex_operation",
    "所有文件处理完成",
    {"processed_files": total_files}
)
```

## 配置选项

系统工具的配置通过 `SystemToolsConfig` 类管理：

```python
from app.tools.system.config import SystemToolsConfig

config = SystemToolsConfig(
    project_root="/home/project",      # 项目根目录
    max_file_size=10 * 1024 * 1024,    # 最大文件大小 (10MB)
    command_timeout=30,                # 命令超时时间 (秒)
    max_output_size=1024 * 1024,       # 最大输出大小 (1MB)
    allowed_commands=frozenset([       # 允许的命令白名单
        "npm", "node", "ls", "cat", "head", "tail"
    ]),
    dangerous_patterns=[               # 危险命令模式
        "rm -rf /", "sudo", "su", "ssh", "scp"
    ]
)
```

## 测试

所有系统工具都有完整的单元测试覆盖：

```bash
# 运行所有系统工具测试
python -m pytest tests/unit/tools/system/ -v

# 运行特定模块测试
python -m pytest tests/unit/tools/system/test_file_operations.py -v
python -m pytest tests/unit/tools/system/test_security.py -v

# 运行演示脚本
python examples/system_tools_demo.py
```

## 集成到 LangGraph

系统工具设计为与 LangGraph 无缝集成：

```python
from langgraph.prebuilt import ToolExecutor
from app.tools.system import (
    save_generated_code, read_project_file,
    execute_npm_command, get_project_status
)

# 创建工具执行器
tools = [
    save_generated_code,
    read_project_file,
    execute_npm_command,
    get_project_status
]

tool_executor = ToolExecutor(tools)
```

## 最佳实践

### 1. 错误处理

```python
result = save_generated_code.invoke({...})

if not result["success"]:
    # 记录错误日志
    logger.error(f"文件保存失败: {result['error']}")

    # 向用户提供友好的错误信息
    user_message = f"抱歉，文件保存失败: {result['error']}"
    return {"error": user_message}
```

### 2. 进度反馈

```python
# 对于长时间运行的操作，提供进度反馈
@with_status_feedback(ProgressType.CODE_GENERATION, "生成项目")
def generate_project():
    # 生成步骤 1
    status_manager.update_progress("project_gen", 25.0, "正在分析需求...")

    # 生成步骤 2
    status_manager.update_progress("project_gen", 50.0, "正在生成代码...")

    # 生成步骤 3
    status_manager.update_progress("project_gen", 75.0, "正在验证代码...")

    # 完成
    return generated_project
```

### 3. 安全检查

```python
# 在执行任何操作前进行安全检查
def safe_operation(file_path, content):
    # 验证路径
    is_safe, abs_path, error = SecurityValidator.validate_path(file_path)
    if not is_safe:
        raise SecurityError(f"路径不安全: {error}")

    # 验证文件大小
    is_safe, error = SecurityValidator.validate_file_size(abs_path, content)
    if not is_safe:
        raise SecurityError(f"文件大小超出限制: {error}")

    # 执行操作
    return save_generated_code.invoke({
        "file_path": file_path,
        "code_content": content
    })
```

## 性能考虑

- ✅ 异步操作支持
- ✅ 文件大小限制防止内存溢出
- ✅ 命令超时防止无限执行
- ✅ 输出大小限制防止响应过大
- ✅ 自动清理完成的操作记录

## 安全考虑

- ✅ 所有文件操作都在项目目录内
- ✅ 命令执行有严格的白名单限制
- ✅ 危险命令模式被自动阻止
- ✅ 所有输入都经过验证和清理
- ✅ 完整的错误处理和日志记录

## 扩展性

系统工具设计为易于扩展：

1. **添加新工具**：创建新的工具文件并添加到 `app/tools/system/`
2. **自定义验证**：扩展 `SecurityValidator` 类添加新的验证规则
3. **状态回调**：使用 `status_manager.add_callback()` 添加自定义状态处理
4. **配置定制**：修改 `SystemToolsConfig` 类调整系统行为