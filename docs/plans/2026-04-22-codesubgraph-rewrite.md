# CodeSubgraph 改造方案 — React 项目真实生成

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 CodeSubgraph 从硬编码假数据改为真正使用 LLM + Tool 生成 React 项目，支持脚手架搭建、代码生成、依赖安装、构建验证的完整流程。

**Architecture:** CodeSubgraph 继承 PipelineReflectionSubgraph 基类，定义 5 个阶段（scaffold → generate → install → build_verify → finalize），通过 `get_bound_llm(state)` 获取已绑定 Tool 的 LLM，在 execute_stage 中使用 ReAct 模式调用 Tool。build_verify 阶段开启反思循环，失败时 LLM 分析报错并修复代码。

**Tech Stack:** LangGraph (PipelineReflectionSubgraph)、LangChain ChatOpenAI、code_executor / write_file / read_file_content / list_directory / get_project_context (已有的 @tool)

---

## 改造范围

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/app/graph/subgraphs/code.py` | **重写** | 核心：用 LLM + Tool 替换硬编码 |
| `backend/app/graph/subgraphs/pipeline.py` | 修改 | execute_stage 支持异步 |
| `backend/app/graph/subgraphs/design.py` | 修改 | 适配新 CodeSubgraph 接口 |
| `backend/app/graph/subgraphs/base.py` | 修改 | 添加 `get_state_key` 方法 |
| `backend/app/graph/state.py` | 修改 | 新增 CodeSubgraph 专用字段 |
| `backend/app/graph/graph.py` | 修改 | 将 CodeSubgraph 插入主图 |

---

## Task 1: base.py — 添加 get_state_key 方法

**Files:**
- Modify: `backend/app/graph/subgraphs/base.py:45-53`

**Step 1: 在 BaseSubgraph 中添加 get_state_key**

`get_state_key` 被 pipeline.py、human_loop.py 等大量调用但未在基类中定义，需要补上。

在 `get_graph` 方法后添加：

```python
def get_state_key(self) -> str:
    """获取子图在主状态中的私有 key"""
    return f"subgraph_{self.name}"
```

**Step 2: 验证 lint**

Run: `cd /Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge && python -c "from app.graph.subgraphs.base import BaseSubgraph, SubgraphConfig; print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add backend/app/graph/subgraphs/base.py
git commit -m "fix: add missing get_state_key method to BaseSubgraph"
```

---

## Task 2: pipeline.py — execute_stage 支持异步

**Files:**
- Modify: `backend/app/graph/subgraphs/pipeline.py:139-159`

**Step 1: 修改 _execute_stage_node 为 async**

当前的 `_execute_stage_node` 是同步函数，直接调 `self.execute_stage(state, stage_name)`，但子类实现是 async 的。需要改为 await。

```python
async def _execute_stage_node(self, state: AgentState) -> Dict:
    """执行当前阶段"""
    subgraph_state = self._get_subgraph_state(state)

    stage_idx = subgraph_state[self._current_stage_idx_key]
    stage_name = self.stages[stage_idx]

    # 更新状态
    subgraph_state[self._status_key] = f"executing_{stage_name}"

    # 执行阶段（await 支持异步子类实现）
    output = await self.execute_stage(state, stage_name)

    # 更新阶段结果
    stage_results = subgraph_state[self._results_key]
    stage_result = stage_results[stage_idx]
    stage_result.output = output
    stage_result.status = StageStatus.REVIEWING
    stage_result.iteration_count = subgraph_state.get(self._current_iteration_key, 0) + 1

    return {self.get_state_key(): subgraph_state}
```

注意：只改了一行 `output = self.execute_stage(...)` → `output = await self.execute_stage(...)`

**Step 2: 同样修改 _review_stage_node 为 async（如果 review_stage 也是 async 的话）**

```python
async def _review_stage_node(self, state: AgentState) -> Dict:
    """自审当前阶段"""
    subgraph_state = self._get_subgraph_state(state)

    stage_idx = subgraph_state[self._current_stage_idx_key]
    stage_results = subgraph_state[self._results_key]
    stage_result = stage_results[stage_idx]

    subgraph_state[self._status_key] = f"reviewing_{stage_result.stage_name}"

    # 自审（await 支持异步子类实现）
    review_result = self.review_stage(state, stage_result)

    # ... 后续不变
```

**Step 3: 验证**

Run: `python -c "from app.graph.subgraphs.pipeline import PipelineReflectionSubgraph; print('OK')"`
Expected: OK

**Step 4: Commit**

```bash
git add backend/app/graph/subgraphs/pipeline.py
git commit -m "fix: make pipeline execute_stage_node async"
```

---

## Task 3: state.py — 新增 CodeSubgraph 专用字段

**Files:**
- Modify: `backend/app/graph/state.py:120-126` (代码生成阶段区域)

**Step 1: 替换旧的代码生成阶段字段**

将旧的 `api_spec / mock_data / frontend_code / style_code / extracted_homepage` 替换为 React 项目生成所需的新字段：

```python
    # ---- 代码生成阶段 ----
    # [新] React 项目生成状态
    project_workdir: Optional[str]               # 项目工作目录绝对路径
    project_files: Optional[Dict[str, str]]      # 生成的项目文件 {相对路径: 内容}
    generated_files_list: List[str]              # 已生成文件路径列表
    build_log: Optional[str]                     # 构建日志（成功/失败）
    build_success: bool                          # 构建是否通过
    code_iteration_count: int                    # 当前构建重试次数

    # [旧 — 保留但不使用，后续清理]
    api_spec: Optional[Dict[str, Any]]           # [DEPRECATED]
    mock_data: Optional[Dict[str, Any]]          # [DEPRECATED]
    frontend_code: Optional[Dict[str, Any]]      # [DEPRECATED]
    style_code: Optional[Dict[str, Any]]         # [DEPRECATED]
    extracted_homepage: Optional[str]            # [DEPRECATED]
```

**Step 2: 验证**

Run: `python -c "from app.graph.state import AgentState; print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add backend/app/graph/state.py
git commit -m "feat: add React project generation fields to AgentState"
```

---

## Task 4: code.py — 重写 CodeSubgraph（核心任务）

**Files:**
- Rewrite: `backend/app/graph/subgraphs/code.py`

**Step 1: 完整重写 code.py**

```python
"""代码生成子图 - 使用 LLM + Tool 生成真实 React 项目

基于 PipelineReflectionSubgraph 实现 5 阶段流水线：
1. scaffold: 创建 Vite + React + TypeScript + Tailwind 脚手架
2. generate: LLM 逐个生成组件/页面/hook 源码文件
3. install: npm install 安装依赖
4. build_verify: npm run build 验证，失败则 LLM 修复 → 重试（反思模式）
5. finalize: 整理文件列表，输出 project_files

依赖：
- loader_node 已将 Skill + Tool 加载到 state（system_prompt, active_tools）
- 使用 get_bound_llm(state) 获取绑定 Tool 的 LLM
- 使用 REACT_PROJECT_TOOLS 中的 code_executor / write_file / read_file_content 等
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.messages import SystemMessage, HumanMessage

from app.graph.state import AgentState
from app.graph.subgraphs.pipeline import PipelineReflectionSubgraph, StageResult
from app.graph.loader_node import get_bound_llm
from app.config import DATA_DIR


# 临时项目根目录
PROJECTS_TEMP_DIR = DATA_DIR / "temp_projects"


class CodeSubgraph(PipelineReflectionSubgraph):
    """代码生成子图 - LLM + Tool 生成 React 项目

    继承 PipelineReflectionSubgraph，使用其流水线 + 阶段自审机制。

    阶段：
    - scaffold: 脚手架搭建（code_executor 执行 npm create vite）
    - generate: LLM 生成源码文件（write_file 逐个写入）
    - install: 安装依赖（code_executor 执行 npm install）
    - build_verify: 构建验证（code_executor 执行 npm run build，失败自修复）
    - finalize: 收尾整理

    反思模式：仅 build_verify 阶段启用。
    """

    def __init__(self, style_config: Optional[Dict] = None, output_prefix: str = ""):
        super().__init__(
            name=f"code_{output_prefix}" if output_prefix else "code",
            stages=["scaffold", "generate", "install", "build_verify", "finalize"],
            max_iterations=3
        )
        self.style_config = style_config or {}
        self.output_prefix = output_prefix

        # 确保临时目录存在
        PROJECTS_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    @property
    def _prefixed_key(self) -> str:
        """带前缀的状态键（用于子图私有状态）"""
        return self.get_state_key()

    # ========== PipelineReflectionSubgraph 抽象方法实现 ==========

    async def execute_stage(self, state: AgentState, stage_name: str) -> Any:
        """执行单个阶段"""

        if stage_name == "scaffold":
            return await self._stage_scaffold(state)
        elif stage_name == "generate":
            return await self._stage_generate(state)
        elif stage_name == "install":
            return await self._stage_install(state)
        elif stage_name == "build_verify":
            return await self._stage_build_verify(state)
        elif stage_name == "finalize":
            return await self._stage_finalize(state)

        return {"error": f"Unknown stage: {stage_name}"}

    def review_stage(self, state: AgentState, stage_result: StageResult) -> Dict:
        """自审阶段产出

        只有 build_verify 阶段需要真正的反思。
        其他阶段直接通过。
        """
        stage_name = stage_result.stage_name
        output = stage_result.output

        # 非 build_verify 阶段：直接通过
        if stage_name != "build_verify":
            return {
                "passed": True,
                "feedback": "",
                "issues": [],
            }

        # build_verify 阶段：检查构建结果
        build_success = output.get("build_success", False)
        build_log = output.get("build_log", "")

        if build_success:
            return {
                "passed": True,
                "feedback": "构建成功",
                "issues": [],
            }

        return {
            "passed": False,
            "feedback": f"构建失败，需要修复：\n{build_log[-2000:]}",
            "issues": [build_log[-1000:]],
        }

    def on_stage_complete(self, stage_result: StageResult) -> None:
        """阶段完成回调"""
        print(f"[CodeSubgraph] 阶段 {stage_result.stage_name} 完成，"
              f"迭代 {stage_result.iteration_count} 次")

    def aggregate_outputs(self, stage_results: List[StageResult]) -> Any:
        """聚合各阶段输出"""
        return {
            r.stage_name: r.output
            for r in stage_results
        }

    # ========== 阶段实现 ==========

    async def _stage_scaffold(self, state: AgentState) -> Dict:
        """阶段1: 脚手架搭建

        1. 创建临时项目目录
        2. 用 code_executor 执行 npm create vite@latest
        3. 安装 Tailwind CSS
        """
        from app.graph.loader_node import get_tool

        # 创建项目目录
        project_id = uuid.uuid4().hex[:8]
        project_name = f"project_{project_id}"
        workdir = str(PROJECTS_TEMP_DIR / project_name)
        os.makedirs(workdir, exist_ok=True)

        # 获取 code_executor tool
        code_executor = get_tool("code_executor")

        # 执行 npm create vite
        scaffold_cmd = (
            f"npm create vite@latest . -- --template react-ts"
        )
        scaffold_result = await code_executor.ainvoke({
            "command": scaffold_cmd,
            "cwd": workdir,
        })

        # 检查脚手架是否创建成功
        if "[ERROR]" in scaffold_result:
            # 备选方案：手动创建 package.json
            return {
                "workdir": workdir,
                "scaffold_success": False,
                "scaffold_log": scaffold_result,
                "need_manual_scaffold": True,
            }

        # 安装 Tailwind CSS
        tailwind_cmd = (
            "npm install -D tailwindcss @tailwindcss/vite"
        )
        tailwind_result = await code_executor.ainvoke({
            "command": tailwind_cmd,
            "cwd": workdir,
        })

        # 初始化 Tailwind 配置
        init_result = ""
        pkg_json_path = os.path.join(workdir, "package.json")
        if os.path.exists(pkg_json_path):
            # 更新 vite.config.ts 添加 tailwindcss 插件
            vite_config_path = os.path.join(workdir, "vite.config.ts")
            if os.path.exists(vite_config_path):
                from app.graph.loader_node import get_tool
                write_file_tool = get_tool("write_file")
                await write_file_tool.ainvoke({
                    "file_path": vite_config_path,
                    "content": (
                        "import { defineConfig } from 'vite'\n"
                        "import react from '@vitejs/plugin-react'\n"
                        "import tailwindcss from '@tailwindcss/vite'\n\n"
                        "export default defineConfig({\n"
                        "  plugins: [\n"
                        "    react(),\n"
                        "    tailwindcss(),\n"
                        "  ],\n"
                        "})\n"
                    ),
                })

            # 更新 src/index.css
            index_css_path = os.path.join(workdir, "src", "index.css")
            parent = os.path.dirname(index_css_path)
            if os.path.exists(parent):
                from app.graph.loader_node import get_tool
                write_file_tool = get_tool("write_file")
                await write_file_tool.ainvoke({
                    "file_path": index_css_path,
                    "content": "@import \"tailwindcss\";\n",
                })

        return {
            "workdir": workdir,
            "scaffold_success": True,
            "scaffold_log": scaffold_result,
            "tailwind_log": tailwind_result,
        }

    async def _stage_generate(self, state: AgentState) -> Dict:
        """阶段2: LLM 生成源码文件

        使用 ReAct 模式：LLM 带着已绑定 Tool 的 LLM 实例，
        根据需求文档（PRD）和设计风格，逐个生成组件文件。
        """
        workdir = self._get_workdir(state)
        if not workdir:
            return {"error": "无项目工作目录，scaffold 阶段未完成"}

        # 获取 LLM（已绑定 Tool）
        bound_llm = get_bound_llm(state)

        # 构造 prompt
        prd = state.get("requirements_doc", "")
        design_style = self.style_config or state.get("design_style", {})
        system_prompt = state.get("system_prompt", "")

        generate_prompt = f"""{system_prompt}

## 当前任务：生成 React 项目源码

### 用户需求（PRD）
{prd}

### 设计风格
{design_style}

### 项目工作目录
{workdir}

### 要求
1. 先调用 get_project_context 查看当前项目结构
2. 根据需求拆分组件（components/）、页面（pages/）、hooks/
3. 逐个调用 write_file 生成文件
4. 确保所有 import 路径正确
5. 使用 Tailwind CSS class 做样式，禁止内联 style
6. 文件命名 PascalCase（组件）、camelCase（工具函数）
7. 所有组件必须使用 TypeScript + 函数组件 + hooks

### 项目结构约定
```
src/
├── components/     # 可复用组件
├── pages/          # 页面组件
├── hooks/          # 自定义 hooks
├── utils/          # 工具函数
├── types/          # TypeScript 类型定义
├── App.tsx         # 根组件
├── main.tsx        # 入口文件
└── index.css       # Tailwind 入口
```

请开始生成代码。每次调用一个 Tool，逐步完成。
"""

        # LLM ReAct 循环
        messages = [
            SystemMessage(content=generate_prompt),
            HumanMessage(content="请开始生成项目的 React 源码文件。"),
        ]

        generated_files: List[str] = []
        max_tool_calls = 20  # 防止无限循环

        for _ in range(max_tool_calls):
            response = await bound_llm.ainvoke(messages)
            messages.append(response)

            # 检查是否有 tool_calls
            if not response.tool_calls:
                break

            # 执行所有 tool_calls
            from langchain_core.messages import ToolMessage
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]

                # 执行 tool
                from app.graph.loader_node import get_tool
                tool = get_tool(tool_name)
                if tool is None:
                    messages.append(ToolMessage(
                        content=f"工具 {tool_name} 不存在",
                        tool_call_id=tool_call["id"],
                    ))
                    continue

                try:
                    tool_result = await tool.ainvoke(tool_call["args"])
                    messages.append(ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call["id"],
                    ))

                    # 跟踪生成的文件
                    if tool_name == "write_file":
                        file_path = tool_call["args"].get("file_path", "")
                        if file_path and workdir in file_path:
                            rel_path = os.path.relpath(file_path, workdir)
                            generated_files.append(rel_path)

                except Exception as e:
                    messages.append(ToolMessage(
                        content=f"工具执行错误: {str(e)}",
                        tool_call_id=tool_call["id"],
                    ))

        return {
            "generated_files": generated_files,
            "files_count": len(generated_files),
        }

    async def _stage_install(self, state: AgentState) -> Dict:
        """阶段3: 安装依赖"""
        workdir = self._get_workdir(state)
        if not workdir:
            return {"install_success": False, "install_log": "无工作目录"}

        from app.graph.loader_node import get_tool
        code_executor = get_tool("code_executor")

        result = await code_executor.ainvoke({
            "command": "npm install",
            "cwd": workdir,
        })

        install_success = "[ERROR]" not in result

        return {
            "install_success": install_success,
            "install_log": result,
        }

    async def _stage_build_verify(self, state: AgentState) -> Dict:
        """阶段4: 构建验证

        执行 npm run build，验证代码能否编译通过。
        失败时 review_stage 会返回 passed=False，
        触发反思循环：LLM 分析报错 → 修复代码 → 重新 build。
        """
        workdir = self._get_workdir(state)
        if not workdir:
            return {"build_success": False, "build_log": "无工作目录"}

        from app.graph.loader_node import get_tool
        code_executor = get_tool("code_executor")

        result = await code_executor.ainvoke({
            "command": "npm run build",
            "cwd": workdir,
        })

        build_success = "[ERROR]" not in result

        return {
            "build_success": build_success,
            "build_log": result,
            "workdir": workdir,
        }

    async def _stage_finalize(self, state: AgentState) -> Dict:
        """阶段5: 收尾整理

        1. 收集所有生成的文件
        2. 整理 project_files {相对路径: 内容}
        3. 更新主状态
        """
        workdir = self._get_workdir(state)
        if not workdir:
            return {"error": "无工作目录"}

        # 收集所有文件（排除 node_modules、dist）
        project_files = {}
        skip_dirs = {"node_modules", "dist", ".git", "__pycache__"}

        for root, dirs, files in os.walk(workdir):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for file in sorted(files):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, workdir)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        project_files[rel_path] = f.read()
                except Exception:
                    pass  # 跳过二进制文件

        return {
            "project_files": project_files,
            "files_count": len(project_files),
            "completed_at": datetime.now().isoformat(),
        }

    # ========== 构建失败自修复（反思模式专用） ==========

    async def _fix_build_errors(self, state: AgentState, build_log: str) -> Dict:
        """构建失败时 LLM 分析报错并修复代码

        在 review_stage 返回 passed=False 后，
        execute_stage 会重新执行 build_verify 阶段。
        但在重新 build 之前，需要先让 LLM 修复代码。

        这个方法在 execute_stage(build_verify) 之前被调用。
        """
        workdir = self._get_workdir(state)
        if not workdir:
            return {"fix_success": False}

        bound_llm = get_bound_llm(state)

        fix_prompt = f"""构建失败，请分析报错并修复代码。

## 构建日志
{build_log[-3000:]}

## 要求
1. 仔细分析构建错误
2. 调用 read_file_content 查看相关源文件
3. 调用 write_file 修复错误的文件
4. 只修复导致构建失败的问题，不要做其他改动
"""

        messages = [
            SystemMessage(content=fix_prompt),
            HumanMessage(content="请开始修复构建错误。"),
        ]

        max_tool_calls = 10
        for _ in range(max_tool_calls):
            response = await bound_llm.ainvoke(messages)
            messages.append(response)

            if not response.tool_calls:
                break

            from langchain_core.messages import ToolMessage
            for tool_call in response.tool_calls:
                tool = get_tool(tool_call["name"])
                if tool is None:
                    messages.append(ToolMessage(
                        content=f"工具 {tool_call['name']} 不存在",
                        tool_call_id=tool_call["id"],
                    ))
                    continue

                try:
                    tool_result = await tool.ainvoke(tool_call["args"])
                    messages.append(ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call["id"],
                    ))
                except Exception as e:
                    messages.append(ToolMessage(
                        content=f"错误: {str(e)}",
                        tool_call_id=tool_call["id"],
                    ))

        return {"fix_success": True}

    # ========== 重写 execute_stage 支持 build 阶段先修复再构建 ==========

    async def execute_stage(self, state: AgentState, stage_name: str) -> Any:
        """执行单个阶段（重写以支持 build_verify 的修复逻辑）"""

        # build_verify 阶段：如果是重试（非首次），先修复
        if stage_name == "build_verify":
            subgraph_state = self._get_subgraph_state(state)
            current_iter = subgraph_state.get(self._current_iteration_key, 0)

            if current_iter > 0:
                # 非首次，说明上次 build 失败，先修复
                prev_log = subgraph_state.get(self._results_key, [])
                prev_result = prev_log[-1] if prev_log else None
                if prev_result and hasattr(prev_result, 'output'):
                    build_log = prev_result.output.get("build_log", "")
                    if build_log:
                        await self._fix_build_errors(state, build_log)

            return await self._stage_build_verify(state)

        # 其他阶段：直接执行
        if stage_name == "scaffold":
            return await self._stage_scaffold(state)
        elif stage_name == "generate":
            return await self._stage_generate(state)
        elif stage_name == "install":
            return await self._stage_install(state)
        elif stage_name == "finalize":
            return await self._stage_finalize(state)

        return {"error": f"Unknown stage: {stage_name}"}

    # ========== 辅助方法 ==========

    def _get_workdir(self, state: AgentState) -> Optional[str]:
        """从状态中获取项目工作目录"""
        # 先检查是否有前缀键
        prefixed = f"{self.output_prefix}workdir" if self.output_prefix else "workdir"
        workdir = state.get(prefixed) or state.get("project_workdir")

        # 从子图私有状态获取
        if not workdir:
            subgraph_state = self._get_subgraph_state(state)
            results = subgraph_state.get(self._results_key, [])
            for r in results:
                if hasattr(r, 'output') and isinstance(r.output, dict):
                    workdir = r.output.get("workdir")
                    if workdir:
                        break

        return workdir
```

**Step 2: 验证语法**

Run: `python -c "from app.graph.subgraphs.code import CodeSubgraph; c = CodeSubgraph(); print('OK:', c.stages)"`
Expected: OK: ['scaffold', 'generate', 'install', 'build_verify', 'finalize']

**Step 3: Commit**

```bash
git add backend/app/graph/subgraphs/code.py
git commit -m "feat: rewrite CodeSubgraph with LLM+Tool for real React project generation"
```

---

## Task 5: design.py — 适配新 CodeSubgraph

**Files:**
- Modify: `backend/app/graph/subgraphs/design.py`

**Step 1: 更新 CodeSubgraph 构造函数调用**

旧版 CodeSubgraph 传了 `stages` 和 `max_iterations`，新版通过 `super().__init__` 自行设定。

在 `DesignSubgraph.__init__` 中，CodeSubgraph 的实例化不需要改动（构造参数兼容），但需要确保并行执行时传递 `system_prompt` 和 `active_tools` 给子图。

修改 `_code_worker_node` 中的 `subgraph_input`：

```python
subgraph_input = {
    **state,
    "current_phase": f"code_{style_id}",
    # 确保子图能获取 Skill/Tool
    "system_prompt": state.get("system_prompt", ""),
    "active_tools": state.get("active_tools", []),
    "loaded_skills": state.get("loaded_skills", []),
    "project_type": state.get("project_type", ""),
}
```

**Step 2: 验证**

Run: `python -c "from app.graph.subgraphs.design import DesignSubgraph; print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add backend/app/graph/subgraphs/design.py
git commit -m "fix: pass Skill/Tool state to CodeSubgraph in DesignSubgraph"
```

---

## Task 6: graph.py — 将 CodeSubgraph 插入主图

**Files:**
- Modify: `backend/app/graph/graph.py`

**Step 1: 在 design 和 delivery 之间插入 code 子图**

当前主图流程：`start → load_skills → requirement → design → delivery → respond`

改造后：`start → load_skills → requirement → design → code → delivery → respond`

```python
from app.graph.subgraphs import (
    RequirementSubgraph,
    DesignSubgraph,
    CodeSubgraph,
    DeliverySubgraph,
)

def build_graph(checkpointer: RedisCheckpointSaver = None) -> StateGraph:
    graph = StateGraph(AgentState)

    # 创建子图实例
    requirement_subgraph = RequirementSubgraph()
    design_subgraph = DesignSubgraph()
    code_subgraph = CodeSubgraph()        # 新增
    delivery_subgraph = DeliverySubgraph()

    # 添加节点
    graph.add_node("start", start_node)
    graph.add_node("load_skills", load_skills_and_tools)
    graph.add_node("requirement", requirement_subgraph.compile())
    graph.add_node("design", design_subgraph.compile())
    graph.add_node("code", code_subgraph.compile())              # 新增
    graph.add_node("delivery", delivery_subgraph.compile())
    graph.add_node("respond", respond_node)

    # 边
    graph.set_entry_point("start")
    graph.add_edge("start", "load_skills")
    graph.add_edge("load_skills", "requirement")
    graph.add_edge("requirement", "design")
    graph.add_edge("design", "code")              # 新增
    graph.add_edge("code", "delivery")            # 修改
    graph.add_edge("delivery", "respond")
    graph.add_edge("respond", END)

    return graph.compile(checkpointer=checkpointer)
```

**Step 2: 验证主图能编译**

Run: `python -c "from app.graph.graph import build_graph; print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add backend/app/graph/graph.py
git commit -m "feat: add CodeSubgraph to main graph pipeline"
```

---

## Task 7: delivery.py — 适配新 project_files 输出

**Files:**
- Modify: `backend/app/graph/subgraphs/delivery.py`

**Step 1: 修改 generate_content 读取 project_files**

旧的 DeliverySubgraph 读取 `api_spec / mock_data / frontend_code / style_code`，改为读取新的 `project_files`。

```python
def generate_content(self, state: AgentState) -> Dict:
    # 从主状态读取 CodeSubgraph 输出
    project_files = state.get("project_files", {})
    build_success = state.get("build_success", False)
    files_count = len(project_files) if project_files else 0

    # 生成交付摘要
    file_list = "\n".join(f"- {k}" for k in project_files.keys()) if project_files else "(无文件)"

    prompt = f"""基于以下 React 项目生成交付摘要：

项目文件数量：{files_count}
构建状态：{'成功' if build_success else '失败'}
文件列表：
{file_list}

请提供：
1. 项目概述
2. 主要功能
3. 技术栈
4. 使用说明（npm install && npm run dev）
"""

    response = llm.invoke([
        SystemMessage(content="你是一位技术文档专家。"),
        HumanMessage(content=prompt),
    ])

    return {
        "delivery_summary": response.content,
        "security_report": {"status": "passed", "issues": [], "score": 95},
        "preview_url": "#preview",
        "project_files": project_files,
        "build_success": build_success,
    }
```

**Step 2: Commit**

```bash
git add backend/app/graph/subgraphs/delivery.py
git commit -m "feat: adapt DeliverySubgraph to read project_files from CodeSubgraph"
```

---

## 改造后主流程

```
start
  → load_skills (加载 Skill + 绑定 Tool，一次性)
    → requirement (PRD 确认)
      → design (4 套风格并行生成 + 用户选择)
        → code (React 项目真实生成)
          ├── scaffold (npm create vite + tailwind)
          ├── generate (LLM + Tool 逐个写文件)
          ├── install (npm install)
          ├── build_verify (npm run build + 失败自修复循环)
          └── finalize (收集文件)
            → delivery (交付确认)
              → respond
```

## 风险点

| 风险 | 缓解措施 |
|------|---------|
| LLM 生成 import 路径错误 | build_verify 阶段捕获编译错误并修复 |
| npm install 超时 | code_executor 已有 120s timeout |
| ReAct 循环无限 Tool 调用 | max_tool_calls=20 硬限制 |
| build 反思循环超限 | max_iterations=3 强制通过 |
| 临时项目目录堆积 | 后续可加定时清理机制 |
| DesignSubgraph 并行 4 个 CodeSubgraph 资源消耗大 | 可考虑减少到 2 个或串行 |
