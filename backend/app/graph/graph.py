from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.agents.unified_agent import UnifiedAgent


# 创建全局统一Agent实例
unified_agent = UnifiedAgent()

async def unified_processing_node(state: AgentState) -> dict:
    """统一处理节点"""
    result = await unified_agent.process(state)
    return result

async def result_processing_node(state: AgentState) -> dict:
    """结果处理节点"""
    # 可以在这里添加额外的结果处理逻辑
    # 比如格式化输出、添加元数据等

    strategy_info = state.get("strategy_info", {})

    # 构建用户友好的响应消息
    response_message = f"任务已完成，使用了{strategy_info.get('name', '未知')}策略。"

    if "error" in state:
        response_message = f"处理过程中出现错误：{state['error']}"

    return {
        **state,
        "response_message": response_message,
        "is_complete": state.get("is_complete", True)
    }

def build_graph() -> StateGraph:
    """构建使用统一Agent的LangGraph工作流"""
    graph = StateGraph(AgentState)

    # 添加统一Agent节点
    graph.add_node("unified_processing", unified_processing_node)
    graph.add_node("result_processing", result_processing_node)

    # 设置流程
    graph.set_entry_point("unified_processing")
    graph.add_edge("unified_processing", "result_processing")
    graph.add_edge("result_processing", END)

    return graph.compile()


# 编译好的图实例 — 全局单例，启动时构建一次
pageforge_graph = build_graph()