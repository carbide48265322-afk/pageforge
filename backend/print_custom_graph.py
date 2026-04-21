from app.graph.graph import pageforge_graph

def print_custom_graph():
    """打印符合我们自定义定义的流程图"""
    print("=" * 80)
    print("PageForge 工作流流程图（符合自定义定义）")
    print("=" * 80)
    print()
    
    # 打印 ASCII 图（隐藏 __start__ 和 __end__）
    print