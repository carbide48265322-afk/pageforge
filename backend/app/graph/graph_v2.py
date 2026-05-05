"""
PageForge Graph v2 — Phase 1 新图

流程：intent_router → thinking → plan → style_picker → code_gen → reply

新图与旧图（graph.py）并存，根据项目类型选择：
- 旧项目（html 单页）→ graph.py
- 新项目（react-vite-app）→ graph_v2.py
"""

from langgraph.graph import StateGraph, END, START
from app.graph.state import AgentState

# 导入新节点模块
from app.graph.nodes.intent_router import intent_router
from app.graph.nodes.thinking import thinking_node
from app.graph.nodes.plan import plan_node
from app.graph.nodes.style_picker import style_picker_node
from app.graph.nodes.code_gen import code_gen_node
from app.graph.nodes.reply import reply_node


def route_by_intent_after_router(state: AgentState) -> str:
    """
    条件边路由：在 intent_router 执行后，根据 intent 决定下一步
    
    路由规则：
    - chat / explain / debug / file_operation / unknown → reply（直接回复）
    - code_gen / code_edit → thinking（进入完整生成流程）
    """
    intent = state.get("intent", "unknown")
    
    if intent in ("code_gen", "code_edit"):
        return "thinking"
    else:
        # chat, explain, debug, file_operation, unknown 都走 reply
        return "reply"


def build_graph_v2() -> StateGraph:
    """构建并编译 v2 图"""
    graph = StateGraph(AgentState)
    
    # 添加节点
    graph.add_node("intent_router", intent_router)   # 意图识别
    graph.add_node("thinking", thinking_node)               # 思维链
    graph.add_node("plan", plan_node)                     # 制定计划
    graph.add_node("style_picker", style_picker_node)       # 风格选择
    graph.add_node("code_gen", code_gen_node)               # 代码生成
    graph.add_node("reply", reply_node)                    # 文本回复
    
    # START → intent_router（固定路径）
    graph.add_edge(START, "intent_router")
    
    # intent_router → 条件边（根据意图决定下一步）
    graph.add_conditional_edges(
        "intent_router",
        route_by_intent_after_router,
        {
            "reply": "reply",
            "thinking": "thinking",
        }
    )
    
    # 线性边（thinking → plan → style_picker → code_gen → reply → END）
    graph.add_edge("thinking", "plan")
    graph.add_edge("plan", "style_picker")
    graph.add_edge("style_picker", "code_gen")
    graph.add_edge("code_gen", "reply")
    graph.add_edge("reply", END)
    
    return graph.compile()


# 新图实例（模块加载时编译）
pageforge_graph_v2 = build_graph_v2()
