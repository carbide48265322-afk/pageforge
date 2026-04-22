"""HomepageGeneratorSubgraph - 单风格首页生成子图

生成特定风格的首页HTML，作为DesignSubgraph的嵌套子图使用。
"""

from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage

from app.graph.state import AgentState
from app.config import llm
from .base import BaseSubgraph, SubgraphMode


class HomepageGeneratorSubgraph(BaseSubgraph):
    """单风格首页生成子图
    
    根据配置的风格参数，生成对应风格的首页HTML。
    """
    
    mode = SubgraphMode.HIERARCHICAL
    
    def __init__(self, style_config: Dict, **kwargs):
        """
        Args:
            style_config: 风格配置 {"id": "", "name": "", "desc": ""}
        """
        self.style_config = style_config
        # 动态设置name，避免冲突
        self._style_id = style_config.get("id", "unknown")
        super().__init__(**kwargs)
    
    @property
    def name(self) -> str:
        return f"homepage_generator_{self._style_id}"
    
    @name.setter
    def name(self, value: str):
        pass
    
    def _build_internal(self):
        """构建子图内部结构"""
        from langgraph.graph import StateGraph, END
        
        graph = StateGraph(AgentState)
        
        # 单节点：生成首页
        graph.add_node("generate", self._generate_node)
        graph.set_entry_point("generate")
        graph.add_edge("generate", END)
        
        return graph
    
    def _generate_node(self, state: AgentState) -> Dict:
        """生成首页
        
        Args:
            state: 当前状态
            
        Returns:
            Dict: 生成的首页HTML和风格信息
        """
        requirements = state.get("requirements_doc", "")
        
        prompt = f"""基于以下产品需求，生成{self.style_config['name']}风格的首页HTML代码：

产品需求：
{requirements}

风格描述：{self.style_config['desc']}

要求：
1. 完整的HTML5结构
2. 内联CSS样式（体现该风格特点）
3. 响应式布局
4. 包含产品核心功能的展示区域
5. 使用模拟数据填充内容

请直接输出完整的HTML代码，包含<style>标签。"""
        
        response = llm.invoke([
            SystemMessage(content=f"你是一位专业的前端开发专家，擅长{self.style_config['name']}风格的网页设计。"),
            HumanMessage(content=prompt),
        ])
        
        return {
            self.get_state_key(): {
                "html": response.content,
                "style_id": self.style_config["id"],
                "style_name": self.style_config["name"],
                "style_desc": self.style_config["desc"]
            }
        }
