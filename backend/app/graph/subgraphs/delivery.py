"""DeliverySubgraph - 交付确认子图

基于 HumanInTheLoopSubgraph 实现：
1. 安全扫描
2. 构建预览环境
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
        
        Args:
            state: 当前状态
            
        Returns:
            Dict: 交付预览内容
        """
        # 从主状态读取CodeSubgraph输出
        project_files = {
            "api_spec": state.get("api_spec", ""),
            "mock_data": state.get("mock_data", ""),
            "frontend_code": state.get("frontend_code", ""),
            "style_code": state.get("style_code", "")
        }
        
        # 安全扫描（简化实现）
        security_report = self._security_scan(project_files)
        
        # 组装完整项目
        assembled_project = self._assemble_project(project_files)
        
        # 生成交付摘要
        prompt = f"""基于以下前端项目生成交付摘要：

API设计：{project_files['api_spec'][:500]}...
前端代码：{project_files['frontend_code'][:500]}...
样式代码：{project_files['style_code'][:300]}...

请提供：
1. 项目概述
2. 主要功能
3. 技术栈
4. 预览说明"""
        
        response = llm.invoke([
            SystemMessage(content="你是一位技术文档专家。"),
            HumanMessage(content=prompt),
        ])
        
        return {
            "delivery_summary": response.content,
            "security_report": security_report,
            "preview_url": "#preview",
            "project_files": project_files,
            "assembled_project": assembled_project
        }
    
    def _security_scan(self, files: Dict) -> Dict:
        """安全扫描（简化实现）"""
        # 实际实现应调用安全扫描工具
        return {
            "status": "passed",
            "issues": [],
            "score": 95
        }
    
    def _assemble_project(self, project_files: Dict) -> Dict:
        """组装完整项目
        
        Args:
            project_files: 各阶段代码文件
            
        Returns:
            Dict: 组装后的项目结构
        """
        # 组装为可运行的前端项目
        return {
            "index.html": self._generate_index_html(project_files),
            "style.css": project_files.get("style_code", ""),
            "app.js": self._generate_app_js(project_files),
            "mock.js": project_files.get("mock_data", "")
        }
    
    def _generate_index_html(self, project_files: Dict) -> str:
        """生成入口HTML"""
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Project</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div id="app"></div>
    <script src="mock.js"></script>
    <script src="app.js"></script>
</body>
</html>"""
    
    def _generate_app_js(self, project_files: Dict) -> str:
        """生成应用JS（整合前端代码）"""
        frontend_code = project_files.get("frontend_code", "")
        # 简单包装，实际可能需要更复杂的处理
        return f"""// Generated App
{frontend_code}

// Initialize
if (typeof initApp === 'function') {{
    initApp();
}}"""
    
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
                "project": content.get("assembled_project", {})
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
