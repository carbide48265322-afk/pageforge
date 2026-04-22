from langgraph.graph import StateGraph, END, START
from app.graph.state import AgentState
from app.graph.nodes import respond_node, start_node
from app.graph.loader_node import load_skills_and_tools
from app.graph.subgraphs import (
    RequirementSubgraph, 
    DesignSubgraph, 
    CodeSubgraph,
    DeliverySubgraph
)
from app.checkpoint import RedisCheckpointSaver


def build_graph(checkpointer: RedisCheckpointSaver = None) -> StateGraph:
    """构建 PageForge LangGraph 工作流
    
    完整流程:
    开始 → 加载 Skill/Tool → 需求理解子图 → 风格设计子图 → 代码生成子图 → 交付确认子图 → 回复
    
    Args:
        checkpointer: Redis 检查点存储器，用于持久化状态，支持服务重启后恢复
    """
    graph = StateGraph(AgentState)

    # 创建子图实例
    requirement_subgraph = RequirementSubgraph()
    design_subgraph = DesignSubgraph()
    code_subgraph = CodeSubgraph()
    delivery_subgraph = DeliverySubgraph()
    
    # 添加节点
    graph.add_node("start", start_node)                           # 开始阶段
    graph.add_node("load_skills", load_skills_and_tools)          # 加载 Skill & Tool
    graph.add_node("requirement", requirement_subgraph.compile()) # 阶段1: 需求理解子图
    graph.add_node("design", design_subgraph.compile())           # 阶段2: 风格设计子图
    graph.add_node("code", code_subgraph.compile())               # 阶段3: 代码生成子图
    graph.add_node("delivery", delivery_subgraph.compile())       # 阶段4: 交付确认子图
    graph.add_node("respond", respond_node)                       # 生成回复

    # 添加边 — 定义节点之间的流转
    graph.set_entry_point("start")                                # 入口 → 开始阶段
    graph.add_edge("start", "load_skills")                        # 开始 → 加载 Skill/Tool
    graph.add_edge("load_skills", "requirement")                  # 加载完成 → 需求理解子图
    graph.add_edge("requirement", "design")                      # 需求确认后 → 设计
    graph.add_edge("design", "code")                             # 设计确认后 → 代码生成
    graph.add_edge("code", "delivery")                           # 代码生成完成 → 交付确认
    graph.add_edge("delivery", "respond")                        # 交付确认后 → 生成回复
    graph.add_edge("respond", END)                               # 回复 → 结束

    return graph.compile(checkpointer=checkpointer)


# 编译好的图实例 — 全局单例，启动时构建一次
# 生产环境应传入 RedisCheckpointSaver 实例
checkpointer = RedisCheckpointSaver()
pageforge_graph = build_graph(checkpointer=checkpointer)


if __name__ == "__main__":
    # 生成流程图
    from langgraph.graph import display_graph
    display_graph(pageforge_graph, output_file="pageforge_workflow.png")
    print("流程图已生成：pageforge_workflow.png")
