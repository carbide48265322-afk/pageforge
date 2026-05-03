# 统一注册中心实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建统一注册中心来管理后端工具和技能系统，提高代码可维护性和扩展性

**Architecture:** 实现 ToolRegistry 类统一管理工具和技能注册，AutoDiscover 类自动发现并注册，改造现有代码使用新注册中心

**Tech Stack:** Python, FastAPI, LangChain, dataclasses

---

## 文件结构映射

**新创建文件:**
- `backend/app/core/registry.py` - 统一注册中心核心类
- `backend/app/core/discovery.py` - 自动发现机制
- `backend/app/core/__init__.py` - 全局实例和初始化
- `tests/unit/core/test_registry.py` - 注册中心单元测试
- `tests/unit/core/test_discovery.py` - 自动发现单元测试

**修改文件:**
- `backend/app/graph/tools.py` - 添加工具注册装饰器
- `backend/app/graph/nodes.py` - 使用注册中心获取工具和技能
- `backend/app/main.py` - 启动时初始化注册中心
- `backend/app/config.py` - 添加工具目录配置

### Task 1: 创建注册中心核心类

**Files:**
- Create: `backend/app/core/registry.py`
- Test: `tests/unit/core/test_registry.py`

- [ ] **Step 1: 创建测试文件**

```python
# tests/unit/core/test_registry.py
import pytest
from unittest.mock import Mock
from app.core.registry import ToolRegistry, ToolInfo, SkillInfo

class TestToolRegistry:
    def test_register_tool(self):
        registry = ToolRegistry()
        
        # 模拟 LangChain 工具
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.description = "A test tool"
        
        registry.register_tool(mock_tool)
        
        assert "test_tool" in registry.list_tools()
        tool_info = registry.get_tool_info("test_tool")
        assert tool_info.name == "test_tool"
        
    def test_register_skill(self):
        registry = ToolRegistry()
        
        registry.register_skill(
            name="test_skill",
            content="Test skill content",
            metadata={"description": "Test skill"}
        )
        
        assert "test_skill" in registry.list_skills()
        assert "Test skill content" in registry.get_skill_guide()
        
    def test_get_langchain_tools(self):
        registry = ToolRegistry()
        
        # 模拟工具
        mock_tool = Mock()
        mock_tool.name = "tool1"
        mock_tool.description = "Tool 1"
        
        registry.register_tool(mock_tool)
        tools = registry.get_langchain_tools()
        
        assert len(tools) == 1
        assert tools[0] == mock_tool
```

- [ ] **Step 2: 运行测试确保失败**

```bash
cd /Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend
pytest tests/unit/core/test_registry.py -v
```

Expected: ModuleNotFoundError - "No module named 'app.core.registry'"

- [ ] **Step 3: 创建注册中心核心类**

```python
# backend/app/core/registry.py
from typing import Dict, List, Any, Callable
from dataclasses import dataclass
import inspect

@dataclass
class ToolInfo:
    """工具信息"""
    name: str
    function: Callable
    description: str
    parameters: Dict[str, Any]

@dataclass  
class SkillInfo:
    """技能信息"""
    name: str
    content: str
    metadata: Dict[str, Any]
    path: str

class ToolRegistry:
    """统一工具注册中心"""
    
    def __init__(self):
        self._tools: Dict[str, ToolInfo] = {}
        self._skills: Dict[str, SkillInfo] = {}
        
    def register_tool(self, tool_fn: Callable) -> Callable:
        """注册工具（装饰器方式）"""
        tool_info = ToolInfo(
            name=tool_fn.name,
            function=tool_fn,
            description=tool_fn.description,
            parameters=self._extract_parameters(tool_fn)
        )
        self._tools[tool_info.name] = tool_info
        return tool_fn
        
    def register_skill(self, name: str, content: str, 
                      metadata: Dict[str, Any] = None,
                      path: str = "") -> None:
        """注册技能"""
        skill_info = SkillInfo(
            name=name,
            content=content,
            metadata=metadata or {},
            path=path
        )
        self._skills[name] = skill_info
        
    def get_langchain_tools(self) -> List:
        """获取 LangChain 工具列表"""
        return [info.function for info in self._tools.values()]
        
    def get_skill_guide(self) -> str:
        """获取合并的技能指南"""
        if not self._skills:
            return ""
            
        guide_parts = []
        for skill in self._skills.values():
            guide_parts.append(f"\n{'='*60}")
            guide_parts.append(f"技能: {skill.name}")
            guide_parts.append(f"{'='*60}")
            guide_parts.append(skill.content)
            
        return "\n".join(guide_parts)
        
    def get_tool_info(self, name: str) -> ToolInfo:
        """获取工具信息"""
        return self._tools.get(name)
        
    def list_tools(self) -> List[str]:
        """列出所有工具名称"""
        return list(self._tools.keys())
        
    def list_skills(self) -> List[str]:
        """列出所有技能名称"""
        return list(self._skills.keys())
        
    def _extract_parameters(self, tool_fn: Callable) -> Dict[str, Any]:
        """提取工具参数信息"""
        # 简化实现，实际可以从工具 schema 中提取
        return {}
```

- [ ] **Step 4: 运行测试确保通过**

```bash
cd /Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend
pytest tests/unit/core/test_registry.py -v
```

Expected: 3 passed

- [ ] **Step 5: 提交**

```bash
cd /Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge
git add backend/app/core/registry.py tests/unit/core/test_registry.py
git commit -m "feat: 创建统一注册中心核心类 ToolRegistry"
```

### Task 2: 创建自动发现机制

**Files:**
- Create: `backend/app/core/discovery.py`
- Test: `tests/unit/core/test_discovery.py`

- [ ] **Step 1: 创建测试文件**

```python
# tests/unit/core/test_discovery.py
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from app.core.discovery import AutoDiscover
from app.core.registry import ToolRegistry

class TestAutoDiscover:
    def test_discover_skills(self, tmp_path):
        # 创建临时技能目录结构
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        
        skill_dir = skills_dir / "test-skill"
        skill_dir.mkdir()
        
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: A test skill
---

Test skill content
""")
        
        registry = ToolRegistry()
        discoverer = AutoDiscover(registry)
        
        discoverer.discover_skills(skills_dir)
        
        assert "test-skill" in registry.list_skills()
        guide = registry.get_skill_guide()
        assert "Test skill content" in guide
        
    def test_discover_tools(self):
        registry = ToolRegistry()
        discoverer = AutoDiscover(registry)
        
        # 模拟工具模块
        mock_tool = Mock()
        mock_tool.name = "mock_tool"
        mock_tool.description = "Mock tool"
        
        with patch('app.core.discovery.Path') as mock_path:
            mock_path.return_value.glob.return_value = []
            discoverer.discover_tools(Path("/fake/tools"))
            
        # 测试空目录情况
        assert len(registry.list_tools()) == 0
```

- [ ] **Step 2: 运行测试确保失败**

```bash
cd /Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend
pytest tests/unit/core/test_discovery.py -v
```

Expected: ModuleNotFoundError - "No module named 'app.core.discovery'"

- [ ] **Step 3: 创建自动发现类**

```python
# backend/app/core/discovery.py
from pathlib import Path
import importlib.util
import re
from app.core.registry import ToolRegistry

class AutoDiscover:
    """自动发现并注册工具/技能"""
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        
    def discover_tools(self, tools_dir: Path) -> None:
        """发现并注册工具"""
        if not tools_dir.exists():
            return
            
        for py_file in tools_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
                
            try:
                module = self._load_module(py_file)
                self._scan_module_for_tools(module)
            except Exception as e:
                print(f"Warning: Failed to load module {py_file}: {e}")
                
    def discover_skills(self, skills_dir: Path) -> None:
        """发现并注册技能"""
        if not skills_dir.exists():
            return
            
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
                
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
                
            try:
                metadata, content = self._parse_skill_file(skill_md)
                self.registry.register_skill(
                    name=skill_dir.name,
                    content=content,
                    metadata=metadata,
                    path=str(skill_dir)
                )
            except Exception as e:
                print(f"Warning: Failed to parse skill {skill_dir}: {e}")
                
    def _load_module(self, py_file: Path):
        """动态加载 Python 模块"""
        spec = importlib.util.spec_from_file_location(
            py_file.stem, py_file
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
        
    def _scan_module_for_tools(self, module):
        """扫描模块中的 LangChain 工具"""
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (hasattr(attr, "name") and 
                hasattr(attr, "description") and
                hasattr(attr, "invoke")):
                # 是 LangChain 工具
                self.registry.register_tool(attr)
                
    def _parse_skill_file(self, skill_path: Path):
        """解析技能文件"""
        content = skill_path.read_text(encoding="utf-8")
        
        # 解析 YAML frontmatter
        metadata = {}
        match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
        if match:
            try:
                import yaml
                metadata = yaml.safe_load(match.group(1)) or {}
            except ImportError:
                # 没有 pyyaml，简单解析
                metadata = self._simple_parse(match.group(1))
                
        # 提取正文内容
        body_match = re.search(r"^---\n.*?\n---\n?", content, re.DOTALL)
        if body_match:
            content = content[body_match.end():].strip()
        else:
            content = content.strip()
            
        return metadata, content
        
    def _simple_parse(self, text: str) -> dict:
        """简单解析 frontmatter"""
        result = {}
        for line in text.strip().split("\n"):
            if ":" in line:
                key, _, value = line.partition(":")
                result[key.strip()] = value.strip().strip("\"'")
        return result
```

- [ ] **Step 4: 运行测试确保通过**

```bash
cd /Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend
pytest tests/unit/core/test_discovery.py -v
```

Expected: 2 passed

- [ ] **Step 5: 提交**

```bash
cd /Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge
git add backend/app/core/discovery.py tests/unit/core/test_discovery.py
git commit -m "feat: 创建自动发现机制 AutoDiscover"
```

### Task 3: 创建全局实例和初始化

**Files:**
- Create: `backend/app/core/__init__.py`
- Modify: `backend/app/config.py:19`

- [ ] **Step 1: 创建全局实例文件**

```python
# backend/app/core/__init__.py
from .registry import ToolRegistry
from .discovery import AutoDiscover

# 全局注册中心实例
registry = ToolRegistry()

# 自动发现器
discoverer = AutoDiscover(registry)

def init_registry():
    """初始化注册中心"""
    from app.config import TOOLS_DIR, SKILLS_DIR
    from pathlib import Path
    
    discoverer.discover_tools(Path(TOOLS_DIR))
    discoverer.discover_skills(Path(SKILLS_DIR))
    
    print(f"[Registry] 已注册工具: {registry.list_tools()}")
    print(f"[Registry] 已注册技能: {registry.list_skills()}")
```

- [ ] **Step 2: 添加工具目录配置**

```python
# backend/app/config.py (在文件末尾添加)

# 工具目录
TOOLS_DIR = BASE_DIR / "app" / "graph"
```

- [ ] **Step 3: 验证配置正确**

```bash
cd /Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend
python -c "from app.config import TOOLS_DIR, SKILLS_DIR; print('TOOLS_DIR:', TOOLS_DIR); print('SKILLS_DIR:', SKILLS_DIR)"
```

Expected: 显示正确的目录路径

- [ ] **Step 4: 提交**

```bash
cd /Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge
git add backend/app/core/__init__.py
git commit -m "feat: 创建全局注册中心实例和初始化函数"
```

### Task 4: 改造现有工具注册

**Files:**
- Modify: `backend/app/graph/tools.py`

- [ ] **Step 1: 添加工具注册装饰器**

```python
# backend/app/graph/tools.py
from langchain_core.tools import tool
from app.core import registry

@tool
@registry.register_tool  # 新增装饰器
def validate_html(html: str) -> dict:
    """验证 HTML 页面的结构和安全性。
    
    检查项目：
    1. 完整的 HTML 结构（DOCTYPE、html、head、body）
    2. viewport meta 标签
    3. 恶意模式扫描（parent.document、eval 注入等）
    4. 基础可访问性（lang 属性、charset）
    
    Args:
        html: 待验证的 HTML 内容
    """
    errors = []

    # 结构检查
    if "<!DOCTYPE html>" not in html and "<html" not in html.lower():
        errors.append("缺少 DOCTYPE 或 html 标签")
    if "<head>" not in html:
        errors.append("缺少 head 标签")
    if "viewport" not in html:
        errors.append("缺少 viewport meta 标签")
    if 'charset' not in html.lower():
        errors.append("缺少 charset 声明")

    # 安全检查 — 扫描恶意模式
    dangerous_patterns = [
        "parent.document",
        "parent.location",
        "parent.window",
        "top.document",
        "top.location",
        "window.parent",
        "document.cookie",
        "navigator.credentials",
    ]
    for pattern in dangerous_patterns:
        if pattern in html:
            errors.append(f"检测到危险模式: {pattern}")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": [],
    }


# Agent 可用的工具列表 — 改为从注册中心获取
AGENT_TOOLS = registry.get_langchain_tools()
```

- [ ] **Step 2: 验证工具注册**

```bash
cd /Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend
python -c "from app.graph.tools import AGENT_TOOLS; print('Registered tools:', len(AGENT_TOOLS))"
```

Expected: 显示注册的工具数量

- [ ] **Step 3: 提交**

```bash
cd /Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge
git add backend/app/graph/tools.py
git commit -m "feat: 改造工具注册使用装饰器"
```

### Task 5: 改造工作流节点使用注册中心

**Files:**
- Modify: `backend/app/graph/nodes.py`

- [ ] **Step 1: 改造技能加载节点**

```python
# backend/app/graph/nodes.py (替换 load_skill_node 函数)

async def load_skill_node(state: AgentState) -> dict:
    """技能加载节点 — 根据用户需求加载相关的技能设计指南
    
    放在意图识别之前执行，确保后续节点都能获取技能指南
    """
    user_message = state["user_message"]
    
    print(f"\n{'='*80}")
    print(f"技能加载节点:")
    print(f"{'='*80}")
    
    # 从注册中心获取技能指南
    from app.core import registry
    skill_guide = registry.get_skill_guide()
    
    print(f"已加载 {len(registry.list_skills())} 个技能")
    print(f"技能内容长度: {len(skill_guide)} 字符")
    print(f"{'='*80}\n")
    
    return {
        "skill_guide": skill_guide,
    }
```

- [ ] **Step 2: 改造执行节点**

```python
# backend/app/graph/nodes.py (替换 execute_node 中的工具获取部分)

async def execute_node(state: AgentState) -> dict:
    """ReAct 执行节点 — 调用 LLM 生成/修改 HTML"""
    
    # ... 前面的代码保持不变 ...
    
    # 从注册中心获取工具
    from app.core import registry
    tools = registry.get_langchain_tools()
    llm_with_tools = llm.bind_tools(tools)
    
    # ... 其余代码保持不变 ...
    
    return {
        "current_html": html,
        "iteration_count": state.get("iteration_count", 0) + 1,
        "fix_count": state.get("fix_count", 0) + (1 if fix_errors else 0),
    }
```

- [ ] **Step 3: 验证节点改造**

```bash
cd /Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend
python -c "from app.graph.nodes import load_skill_node, execute_node; print('Nodes imported successfully')"
```

Expected: 无错误导入

- [ ] **Step 4: 提交**

```bash
cd /Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge
git add backend/app/graph/nodes.py
git commit -m "feat: 改造工作流节点使用注册中心"
```

### Task 6: 改造主程序初始化注册中心

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: 添加注册中心初始化**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.sessions import router as sessions_router
from app.api.messages import router as messages_router
from app.core import init_registry  # 新增导入

app = FastAPI(title="PageForge", version="0.1.0")

# CORS 配置 — 允许前端开发服务器跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite 默认端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(sessions_router, prefix="/api/sessions", tags=["sessions"])
app.include_router(messages_router, prefix="/api/sessions", tags=["messages"])

# 启动时初始化注册中心
@app.on_event("startup")
async def startup():
    """启动时初始化注册中心"""
    init_registry()


@app.get("/api/health")
async def health():
    """健康检查接口"""
    return {"status": "ok"}
```

- [ ] **Step 2: 验证启动初始化**

```bash
cd /Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend
python -c "import uvicorn; from app.main import app; print('App imported successfully with registry initialization')"
```

Expected: 无错误导入

- [ ] **Step 3: 提交**

```bash
cd /Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge
git add backend/app/main.py
git commit -m "feat: 添加注册中心启动初始化"
```

### Task 7: 清理和优化

**Files:**
- Modify: `backend/app/skills/loader.py` (可选清理)

- [ ] **Step 1: 移除不再需要的技能工具转换功能**

```python
# backend/app/skills/loader.py (保留 SkillAutoLoader 类，移除 create_skill_tools 函数)

# 删除或注释掉 create_skill_tools 函数，因为我们不再需要
# def create_skill_tools(skills_dir: str | Path) -> list:
#     """将所有 Skill 转换为 LangChain Tools"""
#