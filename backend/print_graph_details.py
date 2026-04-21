from app.graph.graph import pageforge_graph

def print_graph_details():
    """打印图形的详细信息"""
    print("=" * 70)
    print("PageForge 工作流详细信息")
    print("=" * 70)
    print()
    
    # 获取图形结构
    graph = pageforge_graph.get_graph()
    
    # 打印所有节点
    print("【节点列表】")
    print("-" * 70)
    for node in graph.nodes:
        print(f"  - {node}")
    print()
    
    # 打印所有边
    print("【边列表】")
    print("-" * 70)
    for edge in graph.edges:
        source = edge.source
        target = edge.target
        print(f"  {source} → {target}")
    print()
    
    # # 打印图形的 Mermaid 格式（如果可用）
    # print("【Mermaid 流程图格式】")
    # print("-" * 70)
    # try:
    #     # 尝试获取 Mermaid 格式
    #     mermaid_graph = graph.draw_mermaid()
    #     print(mermaid_graph)
    # except Exception as e:
    #     print(f"无法获取 Mermaid 格式: {e}")
    #     print()
    #     # 手动创建 Mermaid 格式
    #     print("graph TD")
    #     print("    start[开始阶段] --> ideate[构想阶段]")
    #     print("    ideate --> intent[意图理解]")
    #     print("    intent --> execute[ReAct执行]")
    #     print("    execute --> validate[质量检查]")
    #     print("    validate -- 有错误 --> execute")
    #     print("    validate -- 通过检查 --> save[保存版本]")
    #     print("    save --> demo[演示阶段]")
    #     print("    demo --> respond[生成回复]")
    #     print("    respond --> END[结束]")
    # print()
    
    # 打印 ASCII 图
    print("【ASCII 流程图】")
    print("-" * 70)
    graph.print_ascii()
    print()
    print("=" * 70)

if __name__ == "__main__":
    print_graph_details()
