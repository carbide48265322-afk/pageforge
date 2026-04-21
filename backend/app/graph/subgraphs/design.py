"""DesignSubgraph - 风格设计子图

基于 HumanInTheLoopSubgraph 实现：
1. AI 生成 3-5 种风格方案
2. 用户选择风格
3. 输出设计规范
4. 用户确认/微调规范
"""

from typing import Any, Dict, List
from langchain_core.messages import SystemMessage, HumanMessage

from app.graph.state import AgentState
from app.config import llm
from .human_loop import HumanInTheLoopSubgraph


class DesignSubgraph(HumanInTheLoopSubgraph):
    """风格设计子图
    
    实现风格方案生成和确认流程。
    """
    
    name = "design"
    description = "风格设计与规范确认"
    max_iterations = 3
    
    def generate_content(self, state: AgentState) -> Dict:
        """生成风格方案
        
        Args:
            state: 当前状态
            
        Returns:
            Dict: 风格方案列表
        """
        requirements_doc = state.get("requirements_doc", "")
        
        # 检查是否已有风格方案（迭代时保留）
        subgraph_state = state.get(self.get_state_key(), {})
        existing_styles = subgraph_state.get("generated_content", {})
        user_response = subgraph_state.get("user_response", {})
        feedback = user_response.get("feedback", "")
        
        if existing_styles and feedback:
            # 迭代模式：根据反馈调整风格方案
            prompt = f"""基于用户反馈调整风格方案：

产品需求：
{requirements_doc}

当前风格方案：
{existing_styles.get('styles', [])}

用户反馈：{feedback}

请调整风格方案，保持3-5个选项，根据反馈进行优化。"""
        else:
            # 首次生成
            prompt = f"""基于产品需求生成3-5种风格设计方案：

产品需求：
{requirements_doc}

请为每个方案提供：
1. 方案名称
2. 风格描述
3. 色彩建议
4. 字体建议
5. 适用场景"""
        
        response = llm.invoke([
            SystemMessage(content="你是一位资深UI/UX设计师，擅长生成多样化的设计风格方案。"),
            HumanMessage(content=prompt),
        ])
        
        # 解析风格方案（简化版，实际需要解析结构化数据）
        styles = self._parse_styles(response.content)
        
        return {
            "styles": styles,
            "raw_content": response.content,
            "version": subgraph_state.get("iteration_count", 0) + 1
        }
    
    def _parse_styles(self, content: str) -> List[Dict]:
        """解析风格方案（简化实现）"""
        # 实际实现需要更复杂的解析逻辑
        return [{"name": f"方案{i+1}", "description": line} 
                for i, line in enumerate(content.split('\n')[:5]) if line.strip()]
    
    def to_schema(self, content: Dict) -> Dict:
        """转换为选择表单 Schema
        
        Args:
            content: 风格方案内容
            
        Returns:
            Dict: JSON Schema 表单定义
        """
        styles = content.get("styles", [])
        
        return {
            "type": "object",
            "title": "请选择设计风格",
            "description": "请查看 AI 生成的风格方案，选择您喜欢的设计方向",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["confirm", "revise"],
                    "title": "操作",
                    "description": "确认选择或要求调整方案"
                },
                "selected_style": {
                    "type": "string",
                    "enum": [s["name"] for s in styles] if styles else ["方案1"],
                    "title": "选择风格方案",
                    "description": "请选择您喜欢的设计风格"
                },
                "feedback": {
                    "type": "string",
                    "title": "调整建议",
                    "description": "如需调整方案，请描述您的需求",
                    "x-display": "textarea"
                }
            },
            "required": ["action"],
            "x-context": {
                "styles": styles,
                "version": content.get("version", 1)
            }
        }
    
    def process_response(self, state: AgentState, response: Dict) -> Dict:
        """处理用户响应
        
        Args:
            state: 当前状态
            response: 用户响应
            
        Returns:
            Dict: 处理后的状态更新
        """
        action = response.get("action", "confirm")
        
        subgraph_state = state.get(self.get_state_key(), {})
        styles = subgraph_state.get("generated_content", {}).get("styles", [])
        
        if action == "confirm":
            # 用户确认，保存选中的风格
            selected_name = response.get("selected_style", "")
            selected_style = next((s for s in styles if s["name"] == selected_name), styles[0] if styles else {})
            
            return {
                "selected_style": selected_name,
                "design_spec": selected_style,
                "design_approved": True,
                "phase": "tech"
            }
        else:
            # 用户要求调整
            return {
                "design_approved": False,
                "phase": "design"
            }
    
    def should_iterate(self, state: AgentState) -> bool:
        """判断是否继续迭代
        
        Args:
            state: 当前状态
            
        Returns:
            bool: 是否迭代
        """
        subgraph_state = state.get(self.get_state_key(), {})
        response = subgraph_state.get("user_response", {})
        action = response.get("action", "confirm")
        
        if action == "revise":
            iteration_count = subgraph_state.get("iteration_count", 0)
            return iteration_count < self.max_iterations
        
        return False
