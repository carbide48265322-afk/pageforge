# 系统工具设计文档

## 1. 概述

本文档定义了PageForge项目系统工具的设计方案，主要用于支持大模型生成的代码文件的安全管理、前端开发命令的安全执行，以及项目状态的监控和反馈。

## 2. 设计目标

### 2.1 核心目标
- **安全文件操作** - 在隔离的沙箱环境中进行文件读写
- **安全命令执行** - 受限的shell命令执行环境
- **项目状态管理** - 实时监控项目构建和运行状态
- **状态反馈机制** - 为前端提供清晰的操作进度反馈

### 2.2 安全约束
- 文件系统隔离在 `/home/project` 目录
- 每个项目在独立沙箱运行
- 命令执行白名单控制
- 操作审计日志记录

## 3. 系统架构

### 3.1 分层架构

```
+------------------+
|   工具接口层      |
|  (LangChain Tools)|
+------------------+
|   安全控制层      |
| (路径/命令验证)   |
+------------------+
|   沙箱执行层      |
| (隔离环境执行)    |
+------------------+
|   项目文件系统    |
| (/home/project)   |
+------------------+
```

### 3.2 组件关系

```
SystemTools
├── FileOperationTools    # 文件操作工具组
├── CommandExecutionTools # 命令执行工具组  
├── ProjectMonitorTools   # 项目监控工具组
├── SecurityValidator     # 安全验证器
└── StatusFeedback        # 状态反馈管理器
```

## 4. 详细设计

### 4.1 文件操作工具组

#### 4.1.1 save_generated_code

**功能**: 保存大模型生成的代码文件

**签名**:
```python
def save_generated_code(file_path: str, code_content: str, 
                       file_type: str = None) -> dict
```

**参数**:
- `file_path`: 相对路径 (如: "src/components/Header.js")
- `code_content`: 生成的代码内容
- `file_type`: 文件类型 (html/css/js/json)

**返回**:
```json
{
    "success": bool,
    "saved_path": str,
    "file_size": int,
    "backup_created": bool,
    "validation": {
        "syntax_valid": bool,
        "security_check": bool,
        "file_type_match": bool
    }
}
```

**安全控制**:
- 路径验证：确保在/home/project内
- 文件类型验证：检查扩展名和内容匹配
- 语法预检查：对代码进行基础语法验证
- 自动备份：创建.bak备份文件

#### 4.1.2 read_project_file

**功能**: 安全读取项目文件

**签名**:
```python
def read_project_file(file_path: str, max_size: int = 512000) -> dict
```

**参数**:
- `file_path`: 文件相对路径
- `max_size`: 最大读取大小限制（默认512KB）

**返回**:
```json
{
    "success": bool,
    "content": str,
    "encoding": str,
    "size": int,
    "last_modified": str,
    "is_text_file": bool
}
```

**安全控制**:
- 文件大小限制防止内存溢出
- 二进制文件检测和处理
- 编码自动检测和转换

#### 4.1.3 create_project_structure

**功能**: 批量创建项目文件结构

**签名**:
```python
def create_project_structure(structure: dict) -> dict
```

**参数**:
```json
{
    "src": {
        "components": ["Header.js", "Footer.js"],
        "pages": ["index.html", "about.html"]
    },
    "public": ["index.html"]
}
```

**返回**:
```json
{
    "success": bool,
    "created_files": list,
    "created_dirs": list,
    "failed_operations": list
}
```

### 4.2 命令执行工具组

#### 4.2.1 execute_npm_command

**功能**: 安全执行npm相关命令

**签名**:
```python
def execute_npm_command(command: str, args: list = None, 
                       timeout: int = 120) -> dict
```

**支持的命令**:
- `install`: npm install
- `lint`: npm run lint  
- `test`: npm run test
- `build`: npm run build
- `dev`: npm run dev

**返回**:
```json
{
    "success": bool,
    "command": str,
    "exit_code": int,
    "stdout": str,
    "stderr": str,
    "execution_time": float,
    "warnings": list,
    "errors": list
}
```

**安全控制**:
- 命令白名单限制
- 执行超时控制
- 输出大小限制
- 工作目录限制在项目目录

#### 4.2.2 execute_node_command

**功能**: 执行Node.js脚本

**签名**:
```python
def execute_node_command(script_path: str, args: list = None) -> dict
```

**安全控制**:
- 脚本路径验证
- 参数安全过滤
- 执行环境隔离

### 4.3 项目监控工具组

#### 4.3.1 check_project_health

**功能**: 检查项目健康状态

**返回**:
```json
{
    "package_json_valid": bool,
    "dependencies_installed": bool,
    "lint_passed": bool,
    "tests_passed": bool,
    "build_successful": bool,
    "dev_server_started": bool,
    "issues": list
}
```

#### 4.3.2 get_project_status

**功能**: 获取项目当前状态

**返回**:
```json
{
    "project_structure": dict,
    "file_count": int,
    "last_operations": list,
    "build_status": "success|failed|pending",
    "test_status": "passed|failed|not_run",
    "dependencies_status": "installed|missing|outdated"
}
```

#### 4.3.3 monitor_build_process

**功能**: 监控构建过程

**返回**:
```json
{
    "build_id": str,
    "status": "running|completed|failed",
    "progress": float,
    "current_step": str,
    "logs": list,
    "estimated_time_remaining": int
}
```

### 4.4 代码质量工具

#### 4.4.1 validate_code_syntax

**功能**: 验证代码语法

**返回**:
```json
{
    "success": bool,
    "syntax_valid": bool,
    "errors": list,
    "warnings": list,
    "suggestions": list
}
```

#### 4.4.2 run_code_quality_checks

**功能**: 运行代码质量检查

**返回**:
```json
{
    "lint_results": dict,
    "format_results": dict,
    "security_scan": dict,
    "overall_score": float,
    "issues_summary": dict
}
```

## 5. 安全设计

### 5.1 路径安全验证

```python
class SecurityValidator:
    PROJECT_ROOT = "/home/project"
    
    @classmethod
    def validate_path(cls, path: str) -> tuple[bool, str]:
        # 路径规范化
        # 范围检查
        # 遍历攻击检测
```

### 5.2 命令安全验证

```python
class CommandValidator:
    ALLOWED_COMMANDS = {
        "npm", "node", "ls", "cat", "grep", "find"
    }
    
    DANGEROUS_PATTERNS = [
        "rm -rf /", "sudo", "su", "> /dev", "| bash"
    ]
```

### 5.3 操作审计

所有工具操作都会记录审计日志：
- 操作类型和时间
- 操作参数（脱敏处理）
- 执行结果
- 安全验证结果

## 6. 状态反馈设计

### 6.1 反馈类型

```python
class StatusFeedback:
    # 文件操作反馈
    file_operation_status(operation, file_path, status)
    
    # 命令执行反馈  
    command_execution_status(command, stage, progress)
    
    # 代码生成反馈
    code_generation_status(stage, details)
```

### 6.2 反馈格式

```json
{
    "type": "file_operation|command_execution|code_generation",
    "operation": "save|read|npm_install|build",
    "status": "started|running|completed|failed",
    "progress": 0.75,
    "message": "正在保存文件...",
    "timestamp": "2026-04-24T10:30:45.123456"
}
```

## 7. 典型使用场景

### 7.1 前端项目生成流程

```python
# 1. 创建项目结构
create_project_structure(project_config)

# 2. 保存生成的代码
save_generated_code("src/App.js", js_code)
save_generated_code("src/styles.css", css_code)

# 3. 验证代码质量
validate_code_syntax("src/App.js")
run_code_quality_checks()

# 4. 安装依赖并构建
execute_npm_command("install")
execute_npm_command("run", ["build"])

# 5. 检查项目状态
status = get_project_status()
```

### 7.2 代码修改流程

```python
# 1. 读取现有代码
existing_code = read_project_file("src/App.js")

# 2. 大模型修改代码
# ...

# 3. 保存修改后的代码
save_generated_code("src/App.js", modified_code)

# 4. 验证修改
validate_code_syntax("src/App.js")
run_code_quality_checks(["src/App.js"])
```

## 8. 错误处理

### 8.1 错误分类

- **路径错误**: 路径无效、超出范围、权限不足
- **文件错误**: 文件不存在、读写失败、格式错误
- **命令错误**: 命令不存在、执行失败、超时
- **验证错误**: 语法错误、安全检查失败

### 8.2 错误响应格式

```json
{
    "success": false,
    "error_type": "path_error|file_error|command_error|validation_error",
    "error_code": "FILE_NOT_FOUND|COMMAND_TIMEOUT|SYNTAX_ERROR",
    "message": "详细的错误描述",
    "suggestion": "修复建议"
}
```

## 9. 性能考虑

### 9.1 资源限制

- **文件大小限制**: 单个文件最大10MB
- **命令超时**: 默认30秒，可配置
- **并发限制**: 同一时间只允许一个命令执行
- **内存限制**: 沙箱环境内存限制

### 9.2 缓存策略

- **文件内容缓存**: 频繁读取的文件缓存
- **命令结果缓存**: 相同命令的结果缓存
- **项目状态缓存**: 定期更新项目状态

## 10. 测试策略

### 10.1 单元测试

- 每个工具的独立功能测试
- 安全验证逻辑测试
- 错误处理测试

### 10.2 集成测试

- 完整工作流程测试
- 安全边界测试
- 性能测试

### 10.3 安全测试

- 路径遍历攻击测试
- 命令注入测试
- 权限提升测试

## 11. 部署考虑

### 11.1 环境要求

- Python 3.13+
- Node.js 18+
- 足够的磁盘空间
- 适当的文件权限

### 11.2 配置管理

```python
SYSTEM_CONFIG = {
    "project_root": "/home/project",
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "command_timeout": 30,
    "allowed_commands": [...],
    "log_level": "INFO"
}
```

---

**版本**: 1.0  
**最后更新**: 2026-04-24  
**状态**: 设计中  
**负责人**: Claude Code