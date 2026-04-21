"""CodeSubgraph - 代码生成子图

基于 PipelineReflectionSubgraph 实现：
1. API设计 → [Reflection循环]
2. DB Schema → [Reflection循环]
3. 后端代码 → [Reflection循环]
4. 前端代码 → [Reflection循环]
5. 样式代码 → [Reflection循环]
6. 质量检查
"""

from typing import Any, Dict, List
from langchain_core.messages import SystemMessage, HumanMessage

from app.graph.state import AgentState
from app.config import llm
from .pipeline import PipelineReflectionSubgraph, StageResult


class CodeSubgraph(PipelineReflectionSubgraph):
    """代码生成子图
    
    实现流水线式代码生成，每阶段包含自审迭代。
    """
    
    name = "code"
    description = "代码生成与质量检查"
    max_stage_iterations = 3
    
    # 定义流水线阶段
    stages = ["api_design", "db_schema", "backend_code", "frontend_code", "style_code"]
    
    def execute_stage(self, state: AgentState, stage_name: str) -> Any:
        """执行阶段
        
        Args:
            state: 当前状态
            stage_name: 阶段名称
            
        Returns:
            Any: 阶段产出
        """
        if stage_name == "api_design":
            return self._api_design_agent(state)
        elif stage_name == "db_schema":
            return self._db_schema_agent(state)
        elif stage_name == "backend_code":
            return self._backend_code_agent(state)
        elif stage_name == "frontend_code":
            return self._frontend_code_agent(state)
        elif stage_name == "style_code":
            return self._style_code_agent(state)
        return {}
    
    def review_stage(self, state: AgentState, stage_result: StageResult) -> Dict:
        """自审阶段
        
        Args:
            state: 当前状态
            stage_result: 阶段执行结果
            
        Returns:
            Dict: 自审结果
        """
        content = stage_result.output
        stage_name = stage_result.stage_name
        
        prompt = f"""审查以下{stage_name}的质量：

{content}

请检查：
1. 完整性
2. 规范性
3. 潜在问题

如有问题请指出，否则返回"通过"。"""
        
        response = llm.invoke([
            SystemMessage(content="你是一位代码审查专家。"),
            HumanMessage(content=prompt),
        ])
        
        feedback = response.content
        passed = "通过" in feedback or "pass" in feedback.lower()
        
        return {
            "passed": passed,
            "feedback": feedback,
            "issues": [] if passed else [feedback]
        }
    
    def _api_design_agent(self, state: AgentState) -> Dict:
        """API设计Agent"""
        requirements = state.get("requirements_doc", "")
        
        prompt = f"""基于以下需求设计RESTful API：

{requirements}

请提供：
1. API端点列表
2. 请求/响应格式
3. 认证方式"""
        
        response = llm.invoke([
            SystemMessage(content="你是一位API设计专家。"),
            HumanMessage(content=prompt),
        ])
        
        return {"api_spec": response.content}
    
    def _db_schema_agent(self, state: AgentState) -> Dict:
        """DB Schema设计Agent"""
        api_spec = state.get("api_spec", "")
        
        prompt = f"""基于以下API设计数据库Schema：

{api_spec}

请提供：
1. 数据表结构
2. 字段定义
3. 关系设计"""
        
        response = llm.invoke([
            SystemMessage(content="你是一位数据库设计专家。"),
            HumanMessage(content=prompt),
        ])
        
        return {"db_schema": response.content}
    
    def _backend_code_agent(self, state: AgentState) -> Dict:
        """后端代码生成Agent"""
        api_spec = state.get("api_spec", "")
        db_schema = state.get("db_schema", "")
        tech_spec = state.get("tech_spec", {})
        
        prompt = f"""基于以下规范生成后端代码：

API规范：
{api_spec}

数据库Schema：
{db_schema}

技术方案：
{tech_spec}

请生成完整的后端代码。"""
        
        response = llm.invoke([
            SystemMessage(content="你是一位后端开发专家。"),
            HumanMessage(content=prompt),
        ])
        
        return {"backend_code": response.content}
    
    def _frontend_code_agent(self, state: AgentState) -> Dict:
        """前端代码生成Agent"""
        requirements = state.get("requirements_doc", "")
        design_spec = state.get("design_spec", {})
        api_spec = state.get("api_spec", "")
        
        prompt = f"""基于以下规范生成前端代码：

需求：
{requirements}

设计规范：
{design_spec}

API规范：
{api_spec}

请生成完整的前端代码。"""
        
        response = llm.invoke([
            SystemMessage(content="你是一位前端开发专家。"),
            HumanMessage(content=prompt),
        ])
        
        return {"frontend_code": response.content}
    
    def _style_code_agent(self, state: AgentState) -> Dict:
        """样式代码生成Agent"""
        design_spec = state.get("design_spec", {})
        frontend_code = state.get("frontend_code", "")
        
        prompt = f"""基于以下规范生成样式代码：

设计规范：
{design_spec}

前端代码：
{frontend_code}

请生成CSS/Tailwind样式代码。"""
        
        response = llm.invoke([
            SystemMessage(content="你是一位CSS/样式专家。"),
            HumanMessage(content=prompt),
        ])
        
        return {"style_code": response.content}
    
    def aggregate_outputs(self, stage_results: List[StageResult]) -> Any:
        """聚合各阶段输出
        
        Returns:
            Dict: 最终项目文件
        """
        result = {}
        for stage_result in stage_results:
            if isinstance(stage_result.output, dict):
                result.update(stage_result.output)
        return result
