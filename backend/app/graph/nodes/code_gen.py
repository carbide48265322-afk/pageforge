"""
Code Gen Node — 代码生成节点

根据计划、风格配置生成多文件 React + Vite + TypeScript 项目。
通过 SSE 推送 tool_call:*/file_created/status:generation_done 事件。
"""

import logging
from langchain_core.messages import SystemMessage, HumanMessage
from .event_emitter import (
    emit_tool_call_start,
    emit_tool_call_end,
    emit_file_created,
    emit_status_generation_done,
)
from app.config import llm  # 向后兼容，新代码建议用 model_router

logger = logging.getLogger(__name__)


def code_gen_node(state: dict) -> dict:
    """
    代码生成节点函数

    输入: state["user_message"], state.get("plan_steps"), state.get("ui_style_config")
    输出: state + files (文件列表) + project_id
    """
    user_message = state.get("user_message", "")
    plan_steps = state.get("plan_steps", [])
    ui_style_config = state.get("ui_style_config", "")
    session_id = state.get("session_id")

    logger.info(f"[CodeGen] 开始生成代码（计划 {len(plan_steps)} 个步骤）")

    # 获取已注册的工具（模拟环境下可能未注册，降级为 mock）
    from app.core.registry import registry
    write_file_info = registry.get_tool_info("write_file")
    run_command_info = registry.get_tool_info("run_command")
    write_file_tool = write_file_info.function if write_file_info else None
    run_command_tool = run_command_info.function if run_command_info else None

    generated_files = []
    install_result = {"success": False, "output": "skipped"}

    # 模拟模式：工具未注册时直接跳过写文件和安装
    _mock_mode = write_file_tool is None

    try:
        # 定义文件生成列表（内容生成与 I/O 解耦）
        file_generators = [
            ("package.json",      "json",       lambda: _generate_package_json(user_message, plan_steps, ui_style_config)),
            ("index.html",        "html",       _generate_index_html),
            ("vite.config.ts",    "typescript", _generate_vite_config),
            ("tsconfig.json",     "json",       _generate_ts_config),
            ("src/App.tsx",       "typescript", lambda: _generate_app_component(user_message, plan_steps, ui_style_config, state)),
            ("src/main.tsx",      "typescript", _generate_main_entry),
            ("src/index.css",     "css",        lambda: _generate_css_styles(ui_style_config)),
        ]

        for file_path, language, content_fn in file_generators:
            # 生成内容
            if file_path == "src/App.tsx":
                emit_tool_call_start(tool_id="code_gen_llm", name="generate_component", input={"file": file_path})
            content = content_fn()
            if file_path == "src/App.tsx":
                emit_tool_call_end(tool_id="code_gen_llm", status="success")

            # 写入文件（mock 模式跳过实际 I/O）
            if write_file_tool is not None:
                result = write_file_tool.invoke({"path": file_path, "content": content, "session_id": session_id})
                if not result.get("success"):
                    continue
            # mock 模式：直接记录文件，不写盘

            generated_files.append({"path": file_path, "type": "file", "language": language})
            emit_file_created(file_path=file_path, name=file_path.split("/")[-1], language=language)

        # 安装依赖（mock 模式跳过）
        if run_command_tool is not None:
            install_result = run_command_tool.invoke({
                "command": "npm",
                "session_id": session_id,
                "args": ["install"]
            })
        else:
            install_result = {"success": True, "output": "mock_mode: skipped"}

        logger.info(f"[CodeGen] 代码生成完成，共 {len(generated_files)} 个文件")

        # 推送生成完成事件
        emit_status_generation_done()

    except Exception as e:
        logger.error(f"[CodeGen] 代码生成失败: {str(e)}")
        # 推送错误状态
        generated_files = [
            {"path": "error.log", "type": "file", "language": "text", "error": str(e)}
        ]

    return {
        **state,
        "files": generated_files,
        "project_id": session_id,
        "status": "generation_done",
        "install_status": "success" if install_result["success"] else "failed",
    }


def _generate_package_json(user_message: str, plan_steps: list, ui_style_config: str) -> str:
    """生成package.json文件"""
    # 基于用户需求和计划步骤推断依赖
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

    # 根据计划步骤添加额外依赖
    plan_text = str(plan_steps).lower()
    if any(keyword in plan_text for keyword in ["router", "routing", "页面"]):
        dependencies["react-router-dom"] = "^6.0.0"

    if any(keyword in plan_text for keyword in ["state", "状态", "redux", "zustand"]):
        dependencies["zustand"] = "^4.0.0"

    if any(keyword in plan_text for keyword in ["style", "样式", "tailwind", "css"]):
        dev_dependencies["tailwindcss"] = "^3.0.0"
        dev_dependencies["@tailwindcss/typography"] = "^0.5.0"

    package_json = {
        "name": "generated-react-app",
        "private": True,
        "version": "0.0.0",
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "tsc && vite build",
            "preview": "vite preview"
        },
        "dependencies": dependencies,
        "devDependencies": dev_dependencies
    }

    import json
    return json.dumps(package_json, indent=2, ensure_ascii=False)


def _generate_index_html() -> str:
    """生成 Vite SPA 入口 HTML"""
    return '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>PageForge App</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>'''


def _generate_vite_config() -> str:
    """生成Vite配置文件"""
    return '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})'''


def _generate_ts_config() -> str:
    """生成TypeScript配置文件"""
    return '''{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}'''


def _generate_main_entry() -> str:
    """生成主入口文件"""
    return '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)'''


def _generate_css_styles(ui_style_config: str) -> str:
    """生成CSS样式文件"""
    # 基于风格配置生成基础样式
    return '''/* 基础重置和变量 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  line-height: 1.6;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}

/* 响应式设计 */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

/* 基础按钮样式 */
.btn {
  display: inline-block;
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  text-decoration: none;
  transition: all 0.2s;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover {
  background-color: #0056b3;
}

/* 卡片样式 */
.card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  padding: 20px;
  margin: 10px 0;
}'''


def _generate_app_component(user_message: str, plan_steps: list, ui_style_config: str, state: dict = None) -> str:
    """生成主要的App组件"""
    # 使用 model_strategy 选择模型（委托给 model_router）
    if state and "model_strategy" in state:
        from app.core.model_router import get_model_for_node
        node_llm = get_model_for_node("code_gen", state)
    else:
        node_llm = llm  # 降级：使用全局 chat 级别

    # 使用LLM生成具体的组件内容
    prompt = f"""你是一个React开发者，需要根据用户需求和计划生成一个React组件。

用户需求: {user_message}

计划步骤: {plan_steps}

UI风格配置: {ui_style_config}

请生成一个完整的React函数组件(App.tsx)，要求：
1. 使用TypeScript
2. 使用函数组件和Hooks
3. 包含基本的交互功能
4. 遵循React最佳实践
5. 组件应该完整且可运行

输出格式：只返回TSX代码，不要包含markdown或其他说明。
"""

    try:
        response = node_llm.invoke([
            SystemMessage(content="你是一个专业的React开发者，擅长创建现代化的React应用。"),
            HumanMessage(content=prompt)
        ])
        return response.content.strip()
    except Exception as e:
        logger.error(f"[CodeGen] App 组件生成失败: {e}")
        # 如果LLM调用失败，返回一个基础的组件
        return '''import React, { useState } from 'react';

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
            <button
              className="btn btn-primary"
              onClick={() => setCount(count + 1)}
            >
              增加
            </button>
            <button
              className="btn"
              style={{ backgroundColor: '#6c757d', color: 'white' }}
              onClick={() => setCount(0)}
            >
              重置
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;'''
