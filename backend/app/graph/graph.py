from langgraph.graph import StateGraph, END, START
from app.graph.state import AgentState
from app.graph.nodes import intent_node, execute_node, validate_node, save_node, respond_node
from app.graph.nodes_human import human_input_node
from app.graph.edges import should_fix, should_wait_human


def build_graph() -> StateGraph:
    """构建 PageForge LangGraph 工作流
    
    流程: 意图理解 → [人机协作] → 执行(生成HTML) → 质量检查 → (修复循环或)保存 → 回复
    """
    graph = StateGraph(AgentState)

    # 添加节点
    graph.add_node("intent", intent_node)           # 意图理解
    graph.add_node("human_input", human_input_node) # 人机协作检查点
    graph.add_node("execute", execute_node)         # ReAct 执行
    graph.add_node("validate", validate_node)       # 质量检查
    graph.add_node("save", save_node)               # 保存版本
    graph.add_node("respond", respond_node)         # 生成回复

    # 添加边 — 定义节点之间的流转
    graph.set_entry_point("intent")                          # 入口 → 意图理解
    graph.add_edge("intent", "human_input")                   # 意图理解 → 人机协作
    
    # 人机协作后的条件边
    graph.add_conditional_edges(
        "human_input",
        should_wait_human,                                    # 判断是否等待用户
        {
            "wait": END,                                      # 等待用户，图结束
            "continue": "execute"                             # 用户已响应，继续执行
        }
    )
    
    graph.add_edge("execute", "validate")                     # 执行 → 质量检查
    graph.add_conditional_edges("validate", should_fix, {     # 质量检查 → 条件路由
        "fix": "execute",   # 有错误 → 回到执行节点修复
        "save": "save",     # 通过检查 → 保存版本
    })
    graph.add_edge("save", "respond")                         # 保存 → 生成回复
    graph.add_edge("respond", END)                            # 回复 → 结束

    return graph.compile()


# 编译好的图实例 — 全局单例，启动时构建一次
pageforge_graph = build_graph()