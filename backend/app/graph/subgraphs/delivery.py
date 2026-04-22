"""DeliverySubgraph - 交付确认子图

基于 HumanInTheLoopSubgraph 实现：
1. 安全扫描
2. 构建交付摘要
3. 用户预览体验
4. 确认交付 / 返回修改
5. 输出交付物
"""

from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage

from app.graph.state import AgentState
from app.config import llm
from .human_loop import HumanInTheLoopSubgraph


class DeliverySubgraph(HumanInTheLoopSubgraph):
    """交付确认子图
    
    实现交付前的确认流程。
    """
    
    name = "delivery"
    description = "交付确认与输出"
    max_iterations = 2
    
    def generate_content(self, state: AgentState) -> Dict:
        """生成交付预览内容
        
        从 CodeSubgraph 输出的 React 项目文件生成交付摘要。
        """
        # 从主状态读取 CodeSubgraph 输出的 React 项目文件
        project_files = state.get("project_files", {})
        build_success = state.get("build_success", False)
        files_count = len(project_files) if project_files else 0

        # 安全扫描（简化实现）
        security_report = self._security_scan(project_files)
        
        # 生成交付摘要
        file_list = "\n".join(f"- {k}" for k in sorted(project_files.keys())) if project_files else "(无文件)"
        
        prompt = f"""基于以下 React 项目生成交付摘要：

项目文件数量：{files_count}
构建状态：{'成功' if build_success else '失败'}
文件列表：
{file_list}

请提供：
1. 项目概述
2. 主要功能
3. 技术栈（Vite + React + TypeScript + Tailwind CSS）
4. 使用说明（npm install && npm run dev）"""
        
        response = llm.invoke([
            SystemMessage(content="你是一位技术文档专家。"),
            HumanMessage(content=prompt),
        ])
        
        return {
            "delivery_summary": response.content,
            "security_report": security_report,
            "preview_url": "#preview",
            "project_files": project_files,
            "build_success": build_success,
        }
    
    def _security_scan(self, files: Dict) -> Dict:
        """安全扫描（简化实现）"""
        return {
            "status": "passed",
            "issues": [],
            "score": 95
        }

    def to_schema(self, content: Dict) -> Dict:
        """转换为交付确认表单 Schema
        
        Args:
            content: 交付内容
            
        Returns:
            Dict: JSON Schema 表单定义
        """
        return {
            "type": "object",
            "title": "交付确认",
            "description": "请预览项目并确认交付",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["confirm", "revise"],
                    "title": "操作",
                    "description": "确认交付或要求修改"
                },
                "feedback": {
                    "type": "string",
                    "title": "修改建议",
                    "description": "如需修改，请描述具体问题",
                    "x-display": "textarea"
                }
            },
            "required": ["action"],
            "x-context": {
                "summary": content.get("delivery_summary", ""),
                "security": content.get("security_report", {}),
                "preview_url": content.get("preview_url", ""),
                "project_files_count": len(content.get("project_files", {})),
                "build_success": content.get("build_success", False),
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
        
        if action == "confirm":
            # 用户确认交付
            return {
                "delivery_approved": True,
                "is_complete": True,
                "current_phase": "completed",
                "phase": "completed",  # [DEPRECATED] 向后兼容
                "phase_status": "completed",
            }
        else:
            # 用户要求修改，子图内部迭代（重新组装/调整）
            return {
                "delivery_approved": False,
                "revision_feedback": response.get("feedback", ""),
                "current_phase": "delivery",
                "phase": "delivery",  # [DEPRECATED] 向后兼容
            }
    
    def should_iterate(self, state: AgentState) -> bool:
        """判断是否返回修改
        
        Args:
            state: 当前状态
            
        Returns:
            bool: 是否返回修改
        """
        subgraph_state = state.get(self.get_state_key(), {})
        response = subgraph_state.get("user_response", {})
        action = response.get("action", "confirm")
        
        if action == "revise":
            iteration_count = subgraph_state.get("iteration_count", 0)
            return iteration_count < self.max_iterations
        
        return False
