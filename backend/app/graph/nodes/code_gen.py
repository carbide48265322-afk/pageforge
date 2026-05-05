"""
Code Gen Node — 代码生成节点（Phase 4）

根据计划、风格配置生成多文件 React + Vite + TypeScript 项目。
通过 SSE 推送 tool_call:*/file_created/status:generation_done 事件。

架构：
  1. 用 LLM 一次性生成所有文件内容（JSON 格式）
  2. 解析 JSON → 逐个写入文件系统（write_file tool）
  3. 安装依赖（run_command tool）
  4. 推送 SSE 事件（每个文件创建 + 生成完成）

LLM 调用使用 stream_llm() 流式推送，与 thinking/plan/reply 节点保持一致。
"""

import json
import logging
import time
from langchain_core.messages import SystemMessage, HumanMessage
from .event_emitter import (
    emit_tool_call_start,
    emit_tool_call_end,
    emit_file_created,
    emit_status_generation_done,
)
from .llm_utils import stream_llm

logger = logging.getLogger(__name__)

# ========== Prompt 加载（统一管理） ==========
from app.prompts import load_prompt, load_prompt_with_identity

_CODE_GEN_SYSTEM_PROMPT = load_prompt_with_identity("04_code_gen_system")
# user prompt 是模板（含 {占位符}），不拼接 identity
_CODE_GEN_USER_TEMPLATE = load_prompt("04_code_gen_user")


def code_gen_node(state: dict) -> dict:
    """
    Code Gen 节点入口：协调多文件生成流程

    流程：
    1. 用 LLM 流式生成所有文件内容（JSON 格式）
    2. 解析 JSON，逐个写入文件系统
    3. 安装依赖
    4. 推送完成事件
    """
    user_message = state.get("user_message", "")
    plan_steps = state.get("plan_steps", [])
    ui_style_config = state.get("ui_style_config", "")
    session_id = state.get("session_id")
    intent = state.get("intent", "code_gen")

    logger.info(f"[CodeGen] 开始生成代码（intent={intent}, 计划 {len(plan_steps)} 个步骤）")

    # 获取已注册的工具
    from app.core.registry import registry
    write_file_info = registry.get_tool_info("write_file")
    run_command_info = registry.get_tool_info("run_command")
    write_file_tool = write_file_info.function if write_file_info else None
    run_command_tool = run_command_info.function if run_command_info else None

    generated_files = []
    install_result = {"success": False, "output": "skipped"}

    try:
        # ── 步骤1: 用 LLM 生成所有文件内容 ──
        files_json = _generate_all_files_via_llm(
            user_message=user_message,
            plan_steps=plan_steps,
            ui_style_config=ui_style_config,
            intent=intent,
        )

        # ── 步骤2: 写入文件 ──
        for file_entry in files_json:
            file_path = file_entry.get("path", "")
            content = file_entry.get("content", "")
            language = file_entry.get("language", _infer_language(file_path))

            if not file_path or not content:
                continue

            # 写入文件（mock 模式跳过实际 I/O）
            if write_file_tool is not None:
                result = write_file_tool.invoke({
                    "path": file_path,
                    "content": content,
                    "session_id": session_id,
                })
                if not result.get("success"):
                    logger.warning(f"[CodeGen] 写入文件失败: {file_path} — {result.get('error', '')}")
                    continue

            generated_files.append({
                "path": file_path,
                "type": "file",
                "language": language,
            })
            emit_file_created(
                file_path=file_path,
                name=file_path.split("/")[-1],
                language=language,
            )
            logger.info(f"[CodeGen] 已生成: {file_path}")

        # ── 步骤3: 安装依赖 ──
        if run_command_tool is not None and generated_files:
            logger.info(f"[CodeGen] 开始安装依赖...")
            install_result = run_command_tool.invoke({
                "command": "npm",
                "session_id": session_id,
                "args": ["install"],
                "timeout": 120,
            })
            logger.info(f"[CodeGen] 安装结果: {install_result.get('success')}")
        else:
            install_result = {"success": True, "output": "mock_mode: skipped"}

        logger.info(f"[CodeGen] 代码生成完成，共 {len(generated_files)} 个文件")

        # ── 步骤4: 推送生成完成事件 ──
        emit_status_generation_done()

    except Exception as e:
        logger.error(f"[CodeGen] 代码生成失败: {str(e)}", exc_info=True)
        generated_files = [
            {"path": "error.log", "type": "file", "language": "text", "error": str(e)}
        ]

    return {
        **state,
        "files": generated_files,
        "project_id": session_id,
        "status": "generation_done",
        "install_status": "success" if install_result.get("success") else "failed",
    }


def _generate_all_files_via_llm(
    user_message: str,
    plan_steps: list,
    ui_style_config: str,
    intent: str,
) -> list[dict]:
    """
    用 LLM 一次性生成所有文件内容，返回 [{path, content, language}, ...]

    输出格式：JSON 数组，每个元素包含 path 和 content
    """
    from app.core.model_router import get_model_for_node

    # 构建 state 用于 model routing
    state = {"model_strategy": {"code_gen": "code_gen"}}

    # 构建 user prompt
    user_prompt = _CODE_GEN_USER_TEMPLATE.format(
        user_message=user_message,
        plan_steps=_format_plan_steps(plan_steps),
        ui_style_config=ui_style_config,
    )

    tool_id = f"code_gen_llm_{int(time.time() * 1000)}"

    # 流式调用 LLM
    full_content = stream_llm(
        node_name="code_gen",
        state=state,
        messages=[
            SystemMessage(content=_CODE_GEN_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ],
        emit_start=lambda: emit_tool_call_start(
            tool_id=tool_id,
            name="generate_all_files",
            input={"files_count": "multiple"},
        ),
        emit_delta=lambda chunk: None,  # code_gen 不推 delta，只推最终结果
        emit_end=lambda full: emit_tool_call_end(
            tool_id=tool_id,
            status="success",
        ),
    )

    if not full_content:
        logger.warning("[CodeGen] LLM 返回空内容，使用降级方案")
        return _fallback_files(user_message, plan_steps, ui_style_config)

    # 解析 LLM 返回的 JSON
    files_json = _parse_llm_files_output(full_content)

    if not files_json:
        logger.warning("[CodeGen] LLM 输出解析失败，使用降级方案")
        return _fallback_files(user_message, plan_steps, ui_style_config)

    logger.info(f"[CodeGen] LLM 生成了 {len(files_json)} 个文件")
    return files_json


def _parse_llm_files_output(raw_text: str) -> list[dict]:
    """
    解析 LLM 返回的文件列表 JSON。

    支持格式：
    1. 纯 JSON 数组: [{"path": "src/App.tsx", "content": "..."}]
    2. Markdown 代码块包裹: ```json\n[{"path": "src/App.tsx", "content": "..."}]\n```
    3. 多个文件用分隔符: ---FILE:src/App.tsx---\ncontent\n---FILE:src/main.tsx---\ncontent
    """
    if not raw_text:
        return []

    text = raw_text.strip()

    # 尝试1: 去除 markdown 代码块
    if text.startswith("```"):
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("["):
                text = part
                break

    # 尝试2: 解析 JSON 数组
    try:
        data = json.loads(text)
        if isinstance(data, list) and len(data) > 0:
            # 验证每个元素有 path 和 content
            valid = [
                entry for entry in data
                if isinstance(entry, dict) and entry.get("path") and entry.get("content")
            ]
            if valid:
                return valid
    except (json.JSONDecodeError, TypeError):
        pass

    # 尝试3: 解析分隔符格式 ---FILE:path---
    files = []
    if "---FILE:" in text:
        sections = text.split("---FILE:")
        for section in sections[1:]:  # 跳过第一个空段
            lines = section.strip().split("\n", 1)
            if len(lines) == 2:
                path = lines[0].strip()
                content = lines[1].strip()
                if path and content:
                    files.append({
                        "path": path,
                        "content": content,
                        "language": _infer_language(path),
                    })
        if files:
            return files

    # 尝试4: 解析 ## filename: path 格式
    files = []
    if "## filename:" in text or "## file:" in text:
        import re
        pattern = r'## file(?:name)?:\s*(.+?)\n(.*?)(?=## file(?:name)?:|$)'
        matches = re.findall(pattern, text, re.DOTALL)
        for path, content in matches:
            path = path.strip()
            content = content.strip()
            if path and content:
                files.append({
                    "path": path,
                    "content": content,
                    "language": _infer_language(path),
                })
        if files:
            return files

    return []


def _format_plan_steps(plan_steps: list) -> str:
    """将计划步骤格式化为可读文本"""
    if not plan_steps:
        return "无特定步骤"

    lines = []
    for i, step in enumerate(plan_steps, 1):
        if isinstance(step, dict):
            label = step.get("label", step.get("name", str(step)))
            step_type = step.get("type", "")
            lines.append(f"{i}. {label}" + (f" ({step_type})" if step_type else ""))
        else:
            lines.append(f"{i}. {step}")
    return "\n".join(lines)


def _infer_language(path: str) -> str:
    """根据文件路径推断编程语言"""
    ext = path.split(".")[-1].lower() if "." in path else ""
    language_map = {
        "ts": "typescript",
        "tsx": "typescript",
        "js": "javascript",
        "jsx": "javascript",
        "json": "json",
        "css": "css",
        "scss": "scss",
        "html": "html",
        "md": "markdown",
        "py": "python",
    }
    return language_map.get(ext, "text")


def _fallback_files(user_message: str, plan_steps: list, ui_style_config: str) -> list[dict]:
    """
    降级方案：当 LLM 生成失败时，返回基础项目文件
    """
    logger.info("[CodeGen] 使用降级文件方案")

    files = []

    # package.json
    dependencies = {
        "react": "^18.2.0",
        "react-dom": "^18.2.0",
    }
    dev_dependencies = {
        "@types/react": "^18.2.0",
        "@types/react-dom": "^18.2.0",
        "@vitejs/plugin-react": "^4.0.0",
        "typescript": "^5.0.0",
        "vite": "^5.0.0",
    }

    plan_text = str(plan_steps).lower()
    if any(kw in plan_text for kw in ["router", "routing", "页面"]):
        dependencies["react-router-dom"] = "^6.0.0"
    if any(kw in plan_text for kw in ["state", "状态", "redux", "zustand"]):
        dependencies["zustand"] = "^4.0.0"

    files.append({
        "path": "package.json",
        "content": json.dumps({
            "name": "generated-react-app",
            "private": True,
            "version": "0.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "tsc && vite build",
                "preview": "vite preview",
            },
            "dependencies": dependencies,
            "devDependencies": dev_dependencies,
        }, indent=2, ensure_ascii=False),
        "language": "json",
    })

    # index.html
    files.append({
        "path": "index.html",
        "content": '<!DOCTYPE html>\n<html lang="en">\n  <head>\n    <meta charset="UTF-8" />\n    <link rel="icon" type="image/svg+xml" href="/vite.svg" />\n    <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n    <title>PageForge App</title>\n  </head>\n  <body>\n    <div id="root"></div>\n    <script type="module" src="/src/main.tsx"></script>\n  </body>\n</html>',
        "language": "html",
    })

    # vite.config.ts
    files.append({
        "path": "vite.config.ts",
        "content": "import { defineConfig } from 'vite'\nimport react from '@vitejs/plugin-react'\n\nexport default defineConfig({\n  plugins: [react()],\n  server: { port: 3000, host: true },\n  build: { outDir: 'dist', sourcemap: true },\n})",
        "language": "typescript",
    })

    # tsconfig.json
    files.append({
        "path": "tsconfig.json",
        "content": '{\n  "compilerOptions": {\n    "target": "ES2020",\n    "useDefineForClassFields": true,\n    "lib": ["ES2020", "DOM", "DOM.Iterable"],\n    "module": "ESNext",\n    "skipLibCheck": true,\n    "moduleResolution": "bundler",\n    "allowImportingTsExtensions": true,\n    "resolveJsonModule": true,\n    "isolatedModules": true,\n    "noEmit": true,\n    "jsx": "react-jsx",\n    "strict": true,\n    "noUnusedLocals": true,\n    "noUnusedParameters": true,\n    "noFallthroughCasesInSwitch": true\n  },\n  "include": ["src"]\n}',
        "language": "json",
    })

    # src/main.tsx
    files.append({
        "path": "src/main.tsx",
        "content": "import React from 'react'\nimport ReactDOM from 'react-dom/client'\nimport App from './App'\nimport './index.css'\n\nReactDOM.createRoot(document.getElementById('root')!).render(\n  <React.StrictMode>\n    <App />\n  </React.StrictMode>,\n)",
        "language": "typescript",
    })

    # src/App.tsx (基础降级)
    files.append({
        "path": "src/App.tsx",
        "content": '''import React, { useState } from 'react';

function App() {
  const [count, setCount] = useState(0);

  return (
    <div className="container">
      <header style={{ padding: '20px 0', textAlign: 'center' }}>
        <h1>欢迎使用 PageForge</h1>
        <p>你的React应用已经成功生成！</p>
      </header>
      <main style={{ padding: '40px 0' }}>
        <div className="card" style={{ maxWidth: '400px', margin: '0 auto' }}>
          <h2>计数器示例</h2>
          <p>当前计数: <strong>{count}</strong></p>
          <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
            <button className="btn btn-primary" onClick={() => setCount(count + 1)}>增加</button>
            <button className="btn" style={{ backgroundColor: '#6c757d', color: 'white' }} onClick={() => setCount(0)}>重置</button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;''',
        "language": "typescript",
    })

    # src/index.css
    files.append({
        "path": "src/index.css",
        "content": '''* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
  -webkit-font-smoothing: antialiased;
  line-height: 1.6;
}
.container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
.btn { display: inline-block; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
.btn-primary { background-color: #007bff; color: white; }
.btn-primary:hover { background-color: #0056b3; }
.card { background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); padding: 20px; margin: 10px 0; }''',
        "language": "css",
    })

    return files
