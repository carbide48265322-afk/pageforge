from langgraph.graph import StateGraph, END, START
from app.graph.state import AgentState
from app.graph.nodes import execute_node, validate_node, save_node, respond_node, start_node, demo_node
from app.graph.edges import should_fix
from app.graph.subgraphs import RequirementSubgraph, DesignSubgraph, TechSubgraph


def build_graph() -> StateGraph:
    """构建 PageForge LangGraph 工作流
    
    流程: 开始 → 需求理解子图 → 风格设计子图 → 技术方案子图 → 执行(生成HTML) → 质量检查 → (修复循环或)保存 → 演示 → 回复
    """
    graph = StateGraph(AgentState)

    # 创建子图实例
    requirement_subgraph = RequirementSubgraph()
    design_subgraph = DesignSubgraph()
    tech_subgraph = TechSubgraph()
    
    # 添加节点
    graph.add_node("start", start_node)                           # 开始阶段
    graph.add_node("requirement", requirement_subgraph.compile()) # 需求理解子图
    graph.add_node("design", design_subgraph.compile())           # 风格设计子图
    graph.add_node("tech", tech_subgraph.compile())               # 技术方案子图
    graph.add_node("execute", execute_node)                       # ReAct 执行
    graph.add_node("validate", validate_node)                     # 质量检查
    graph.add_node("save", save_node)                             # 保存版本
    graph.add_node("demo", demo_node)                             # 演示阶段
    graph.add_node("respond", respond_node)                       # 生成回复

    # 添加边 — 定义节点之间的流转
    graph.set_entry_point("start")                                # 入口 → 开始阶段
    graph.add_edge("start", "requirement")                       # 开始 → 需求理解子图
    graph.add_edge("requirement", "design")                      # 需求确认后 → 设计
    graph.add_edge("design", "tech")                             # 设计确认后 → 技术方案
    graph.add_edge("tech", "execute")                            # 技术确认后 → 执行
    
    graph.add_edge("execute", "validate")                        # 执行 → 质量检查
    graph.add_conditional_edges("validate", should_fix, {        # 质量检查 → 条件路由
        "fix": "execute",   # 有错误 → 回到执行节点修复
        "save": "save",     # 通过检查 → 保存版本
    })
    graph.add_edge("save", "demo")                               # 保存 → 演示
    graph.add_edge("demo", "respond")                            # 演示 → 生成回复
    graph.add_edge("respond", END)                               # 回复 → 结束

    return graph.compile()


# 编译好的图实例 — 全局单例，启动时构建一次
pageforge_graph = build_graph()


if __name__ == "__main__":
    # 生成流程图
    from langgraph.graph import display_graph
    display_graph(pageforge_graph, output_file="pageforge_workflow.png")
    print("流程图已生成：pageforge_workflow.png")
