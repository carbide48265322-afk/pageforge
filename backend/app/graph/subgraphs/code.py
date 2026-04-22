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
from typing import Any, Dict, List, Optional

from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

from app.graph.state import AgentState
from app.graph.subgraphs.pipeline import PipelineReflectionSubgraph, StageResult
from app.graph.loader_node import get_bound_llm, get_tool
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

    def __init__(self, output_prefix: str = ""):
        super().__init__(
            name=f"code_{output_prefix}" if output_prefix else "code",
            stages=["scaffold", "generate", "install", "build_verify", "finalize"],
            max_iterations=3
        )
        self.output_prefix = output_prefix

        # 确保临时目录存在
        PROJECTS_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # ========== PipelineReflectionSubgraph 抽象方法实现 ==========

    async def execute_stage(self, state: AgentState, stage_name: str) -> Any:
        """执行单个阶段

        build_verify 阶段：如果是重试（非首次），先让 LLM 修复代码再构建。
        """
        # build_verify 阶段：如果是重试（非首次），先修复
        if stage_name == "build_verify":
            subgraph_state = self._get_subgraph_state(state)
            current_iter = subgraph_state.get(self._current_iteration_key, 0)

            if current_iter > 0:
                # 非首次，说明上次 build 失败，先修复
                prev_results = subgraph_state.get(self._results_key, [])
                prev_result = prev_results[-1] if prev_results else None
                if prev_result and hasattr(prev_result, 'output'):
                    build_log = prev_result.output.get("build_log", "")
                    if build_log:
                        await self._fix_build_errors(state, build_log)

            return await self._stage_build_verify(state)

        # 其他阶段：直接执行
        handlers = {
            "scaffold": self._stage_scaffold,
            "generate": self._stage_generate,
            "install": self._stage_install,
            "finalize": self._stage_finalize,
        }

        handler = handlers.get(stage_name)
        if handler:
            return await handler(state)

        return {"error": f"Unknown stage: {stage_name}"}

    async def review_stage(self, state: AgentState, stage_result: StageResult) -> Dict:
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
        build_success = output.get("build_success", False) if isinstance(output, dict) else False
        build_log = output.get("build_log", "") if isinstance(output, dict) else ""

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
        3. 配置 Tailwind CSS
        """
        # 创建项目目录
        project_id = uuid.uuid4().hex[:8]
        project_name = f"project_{project_id}"
        workdir = str(PROJECTS_TEMP_DIR / project_name)
        os.makedirs(workdir, exist_ok=True)

        # 获取 code_executor tool
        code_executor = get_tool("code_executor")
        if not code_executor:
            return {
                "workdir": workdir,
                "scaffold_success": False,
                "scaffold_log": "code_executor tool not found",
            }

        # 执行 npm create vite
        scaffold_cmd = "npm create vite@latest . -- --template react-ts"
        try:
            scaffold_result = await code_executor.ainvoke({
                "command": scaffold_cmd,
                "cwd": workdir,
            })
            scaffold_result_str = str(scaffold_result)
        except Exception as e:
            scaffold_result_str = str(e)

        # 检查脚手架是否创建成功
        scaffold_success = "[ERROR]" not in scaffold_result_str and "package.json" in scaffold_result_str

        # 安装 Tailwind CSS
        tailwind_result_str = ""
        if scaffold_success:
            tailwind_cmd = "npm install -D tailwindcss @tailwindcss/vite"
            try:
                tailwind_result = await code_executor.ainvoke({
                    "command": tailwind_cmd,
                    "cwd": workdir,
                })
                tailwind_result_str = str(tailwind_result)
            except Exception as e:
                tailwind_result_str = str(e)

            # 更新 vite.config.ts 添加 tailwindcss 插件
            vite_config_path = os.path.join(workdir, "vite.config.ts")
            write_file_tool = get_tool("write_file")
            if write_file_tool and os.path.exists(vite_config_path):
                try:
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
                except Exception:
                    pass

            # 更新 src/index.css
            index_css_path = os.path.join(workdir, "src", "index.css")
            if write_file_tool and os.path.exists(os.path.dirname(index_css_path)):
                try:
                    await write_file_tool.ainvoke({
                        "file_path": index_css_path,
                        "content": "@import \"tailwindcss\";\n",
                    })
                except Exception:
                    pass

        return {
            "workdir": workdir,
            "scaffold_success": scaffold_success,
            "scaffold_log": scaffold_result_str,
            "tailwind_log": tailwind_result_str,
        }

    async def _stage_generate(self, state: AgentState) -> Dict:
        """阶段2: LLM 生成源码文件

        使用 ReAct 模式：LLM 带着已绑定 Tool 的实例，
        根据需求文档（PRD）和设计风格，逐个生成组件文件。
        """
        workdir = self._get_workdir(state)
        if not workdir:
            return {"error": "无项目工作目录，scaffold 阶段未完成"}

        # 获取 LLM（已绑定 Tool）
        bound_llm = get_bound_llm(state)

        # 构造 prompt
        prd = state.get("requirements_doc", "")
        design_style = state.get("design_style", {})
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
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
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

        code_executor = get_tool("code_executor")
        if not code_executor:
            return {"install_success": False, "install_log": "code_executor tool not found"}

        try:
            result = await code_executor.ainvoke({
                "command": "npm install",
                "cwd": workdir,
            })
            result_str = str(result)
        except Exception as e:
            result_str = str(e)

        install_success = "[ERROR]" not in result_str

        return {
            "install_success": install_success,
            "install_log": result_str,
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

        code_executor = get_tool("code_executor")
        if not code_executor:
            return {"build_success": False, "build_log": "code_executor tool not found"}

        try:
            result = await code_executor.ainvoke({
                "command": "npm run build",
                "cwd": workdir,
            })
            result_str = str(result)
        except Exception as e:
            result_str = str(e)

        build_success = "[ERROR]" not in result_str

        return {
            "build_success": build_success,
            "build_log": result_str,
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
        project_files: Dict[str, str] = {}
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
        """
        workdir = self._get_workdir(state)
        if not workdir:
            return {"fix_success": False}

        bound_llm = get_bound_llm(state)

        fix_prompt = f"""构建失败，请分析报错并修复代码。

## 构建日志
{build_log[-3000:]}

## 项目工作目录
{workdir}

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

    # ========== 辅助方法 ==========

    def _get_workdir(self, state: AgentState) -> Optional[str]:
        """从状态中获取项目工作目录"""
        # 先检查主状态
        workdir = state.get("project_workdir")

        # 从子图私有状态获取（scaffold 阶段产出）
        if not workdir:
            subgraph_state = self._get_subgraph_state(state)
            results = subgraph_state.get(self._results_key, [])
            for r in results:
                if hasattr(r, 'output') and isinstance(r.output, dict):
                    workdir = r.output.get("workdir")
                    if workdir:
                        break

        return workdir
