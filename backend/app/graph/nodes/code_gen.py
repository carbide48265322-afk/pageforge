"""
Code Gen Node — 代码生成节点

根据计划、风格配置生成多文件 React + Vite + TypeScript 项目。
通过 SSE 推送 file_created / file_updated / status_* 事件。
"""

import logging

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

    logger.info(f"[CodeGen] 开始生成代码（计划 {len(plan_steps)} 个步骤）")

    # TODO: 调用 LLM 生成多文件代码
    # 当前为占位实现：
    # 1. 构造包含风格配置的 Prompt
    # 2. 调用 LLM 生成文件列表
    # 3. 通过 SSE 推送 file_created 事件
    # 4. 推送 status:generation_done 事件

    # 占位文件列表
    files = [
        {"type": "file", "name": "package.json", "path": "frontend/package.json", "language": "json"},
        {"type": "file", "name": "vite.config.ts", "path": "frontend/vite.config.ts", "language": "typescript"},
        {"type": "file", "name": "App.tsx", "path": "frontend/src/App.tsx", "language": "typescript"},
    ]

    logger.info(f"[CodeGen] 代码生成完成，共 {len(files)} 个文件")

    return {
        **state,
        "files": files,
        "project_id": state.get("session_id"),
        "status": "generation_done",
    }
