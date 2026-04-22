"""RequirementSubgraph - 需求理解子图

基于 HumanInTheLoopSubgraph 实现：
1. AI 生成 PRD
2. PRD 转换为表单 Schema
3. 等待用户确认/修改
4. 支持最多3次 AI 内部迭代
"""

from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage

from app.graph.state import AgentState
from app.config import llm
from .human_loop import HumanInTheLoopSubgraph


class RequirementSubgraph(HumanInTheLoopSubgraph):
    """需求理解子图
    
    实现需求澄清和 PRD 确认流程。
    """
    
    name = "requirement"
    description = "需求理解与 PRD 确认"
    max_iterations = 3
    
    def generate_content(self, state: AgentState) -> Dict:
        """生成 PRD 内容
        
        Args:
            state: 当前状态
            
        Returns:
            Dict: PRD 文档结构
        """
        user_message = state.get("user_message", "")
        
        # 检查是否已有 PRD（迭代时保留）
        subgraph_state = state.get(self.get_state_key(), {})
        existing_prd = subgraph_state.get("generated_content", {})
        
        # 检查是否有用户反馈（迭代时）
        user_response = subgraph_state.get("user_response", {})
        feedback = user_response.get("feedback", "")
        
        if existing_prd and feedback:
            # 迭代模式：根据反馈修改 PRD
            prompt = f"""基于用户反馈修改 PRD：

用户原始需求：{user_message}

当前 PRD：
{existing_prd.get('content', '')}

用户反馈：{feedback}

请修改 PRD，保持原有结构，根据反馈进行调整。"""
        else:
            # 首次生成
            prompt = f"""基于用户需求生成详细的产品需求文档：

用户需求：{user_message}

请生成以下内容：
1. 项目概述
2. 功能需求
3. 非功能需求
4. 页面结构设计
5. 交互设计要点

用清晰的 Markdown 格式输出。"""
        
        # 调用 LLM 生成
        response = llm.invoke([
            SystemMessage(content="你是一位专业的产品经理，擅长生成详细的产品需求文档。"),
            HumanMessage(content=prompt),
        ])
        
        prd_content = response.content.strip()
        
        return {
            "content": prd_content,
            "title": "产品需求文档",
            "version": subgraph_state.get("iteration_count", 0) + 1
        }
    
    def to_schema(self, content: Dict) -> Dict:
        """PRD 转换为表单 Schema
        
        Args:
            content: PRD 内容
            
        Returns:
            Dict: JSON Schema 表单定义
        """
        return {
            "type": "object",
            "title": "请确认需求文档",
            "description": "请查看 AI 生成的需求文档，确认或提出修改意见",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["confirm", "revise"],
                    "title": "操作",
                    "description": "确认文档或要求修改"
                },
                "feedback": {
                    "type": "string",
                    "title": "修改建议",
                    "description": "如需修改，请描述需要调整的地方",
                    "x-display": "textarea"
                }
            },
            "required": ["action"],
            "x-context": {
                "prd_content": content.get("content", ""),
                "prd_version": content.get("version", 1)
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
        prd_content = subgraph_state.get("generated_content", {}).get("content", "")
        
        if action == "confirm":
            # 用户确认，保存 PRD 到主状态
            return {
                "requirements_doc": prd_content,
                "requirements_approved": True,
                "current_phase": "design",
                "phase": "design",  # [DEPRECATED] 向后兼容
                "phase_status": "running",
            }
        else:
            # 用户要求修改，保留反馈用于迭代
            return {
                "requirements_approved": False,
                "current_phase": "requirement",
                "phase": "requirement",  # [DEPRECATED] 向后兼容
            }
    
    def should_iterate(self, state: AgentState) -> bool:
        """判断是否继续迭代
        
        Args:
            state: 当前状态
            
        Returns:
            bool: 是否迭代
        """
        subgraph_state = state.get(self.get_state_key(), {})
        
        # 检查用户操作
        response = subgraph_state.get("user_response", {})
        action = response.get("action", "confirm")
        
        # 用户要求修改，且未达到最大迭代次数
        if action == "revise":
            iteration_count = subgraph_state.get("iteration_count", 0)
            return iteration_count < self.max_iterations
        
        return False
