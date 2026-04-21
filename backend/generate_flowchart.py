import sys
import pydot
from app.graph.graph import pageforge_graph

def print_ascii_graph():
    """使用 LangGraph 内置方法打印 ASCII 流程图"""
    print("=" * 60)
    print("PageForge 工作流 ASCII 流程图")
    print("=" * 60)
    print()
    
    # 使用 graph.get_graph().print_ascii() 打印流程图
    # 注意：LangGraph 的 StateGraph 对象需要先获取图形结构
    try:
        graph_structure = pageforge_graph.get_graph()
        graph_structure.print_ascii()
        print()
        print("=" * 60)
        print("ASCII 流程图打印完成！")
        print("=" * 60)
    except Exception as e:
        print(f"打印 ASCII 流程图时出错: {e}")
        print()
        print("尝试使用替代方法...")
        print_graph_info()

def print_graph_info():
    """打印图形信息的替代方法"""
    print("\n工作流节点:")
    print("- start: 开始阶段")
    print("- ideate: 构想阶段")
    print("- intent: 意图理解")
    print("- execute: ReAct 执行")
    print("- validate: 质量检查")
    print("- save: 保存版本")
    print("- demo: 演示阶段")
    print("- respond: 生成回复")
    print("- END: 结束")
    
    print("\n工作流边:")
    print("start → ideate → intent → execute → validate")
    print("validate → (有错误) execute")
    print("validate → (通过) save → demo → respond → END")

def generate_png_graph():
    """使用 pydot 生成 PNG 流程图（备用方法）"""
    # 创建图形
    graph = pydot.Dot(graph_type='digraph', rankdir='LR')
    
    # 添加节点
    start_node = pydot.Node('start', label='开始阶段', shape='box', style='filled', fillcolor='#E6F7FF')
    ideate_node = pydot.Node('ideate', label='构想阶段', shape='box', style='filled', fillcolor='#F6FFED')
    intent_node = pydot.Node('intent', label='意图理解', shape='box', style='filled', fillcolor='#FFF7E6')
    execute_node = pydot.Node('execute', label='ReAct 执行', shape='box', style='filled', fillcolor='#F9F0FF')
    validate_node = pydot.Node('validate', label='质量检查', shape='box', style='filled', fillcolor='#FFE6E6')
    save_node = pydot.Node('save', label='保存版本', shape='box', style='filled', fillcolor='#E6FFFB')
    demo_node = pydot.Node('demo', label='演示阶段', shape='box', style='filled', fillcolor='#FFFFE6')
    respond_node = pydot.Node('respond', label='生成回复', shape='box', style='filled', fillcolor='#E8E8E8')
    end_node = pydot.Node('end', label='结束', shape='ellipse', style='filled', fillcolor='#D9D9D9')
    
    # 添加边
    graph.add_edge(pydot.Edge(start_node, ideate_node, label='开始 → 构想'))
    graph.add_edge(pydot.Edge(ideate_node, intent_node, label='构想 → 意图理解'))
    graph.add_edge(pydot.Edge(intent_node, execute_node, label='意图理解 → 执行'))
    graph.add_edge(pydot.Edge(execute_node, validate_node, label='执行 → 质量检查'))
    graph.add_edge(pydot.Edge(validate_node, execute_node, label='有错误 → 修复'))
    graph.add_edge(pydot.Edge(validate_node, save_node, label='通过检查 → 保存'))
    graph.add_edge(pydot.Edge(save_node, demo_node, label='保存 → 演示'))
    graph.add_edge(pydot.Edge(demo_node, respond_node, label='演示 → 回复'))
    graph.add_edge(pydot.Edge(respond_node, end_node, label='回复 → 结束'))
    
    # 保存为PNG文件
    try:
        graph.write_png('pageforge_workflow.png')
        print("\nPNG 流程图已生成：pageforge_workflow.png")
    except Exception as e:
        print(f"\n生成 PNG 流程图时出错: {e}")
        print("提示：可能需要安装 Graphviz 软件")

if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "png":
            generate_png_graph()
        elif sys.argv[1] == "both":
            print_ascii_graph()
            print()
            generate_png_graph()
    else:
        print_ascii_graph()
