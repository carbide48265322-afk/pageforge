from typing import Dict, Any
from dataclasses import dataclass
from app.config import llm
from langchain_core.messages import HumanMessage

@dataclass
class TaskAnalysis:
    """任务分析结果"""
    complexity: float  # 0-1, 任务复杂度
    structured: float  # 0-1, 结构化程度
    needs_tools: bool  # 是否需要工具调用
    creativity: float  # 0-1, 创造性需求
    certainty: float   # 0-1, 结果确定性
    estimated_steps: int  # 预估步骤数
    domain: str        # 任务领域
    confidence: float  # 0-1, 分析置信度

class TaskAnalyzer:
    """任务分析器 - 分析用户需求的特征"""

    def __init__(self):
        self.analysis_llm = llm  # 使用轻量级LLM进行分析

    async def analyze_task(self, user_message: str) -> TaskAnalysis:
        """分析任务特征"""
        analysis_prompt = self._build_analysis_prompt(user_message)

        try:
            response = await self.analysis_llm.ainvoke([
                HumanMessage(content=analysis_prompt)
            ])

            analysis_data = self._parse_analysis_response(response.content)
            return TaskAnalysis(**analysis_data)

        except Exception as e:
            # 分析失败时使用默认值
            return self._get_default_analysis(user_message)

    def _build_analysis_prompt(self, user_message: str) -> str:
        """构建分析提示"""
        return f"""分析以下用户需求的特征，返回JSON格式：

用户需求: "{user_message}"

请评估以下维度（0-1分）：
1. complexity: 任务复杂度（简单=0，非常复杂=1）
2. structured: 结构化程度（模糊=0，步骤清晰=1）
3. needs_tools: 是否需要调用外部工具（true/false）
4. creativity: 创造性需求（常规=0，高度创新=1）
5. certainty: 结果确定性（不确定=0，结果明确=1）
6. estimated_steps: 预估需要的步骤数（整数）
7. domain: 任务领域（如"frontend", "html", "fullstack", "general"）
8. confidence: 分析置信度（0-1）

示例输出：
{{
  "complexity": 0.7,
  "structured": 0.8,
  "needs_tools": true,
  "creativity": 0.3,
  "certainty": 0.9,
  "estimated_steps": 5,
  "domain": "frontend",
  "confidence": 0.85
}}

请只返回JSON，不要其他内容："""

    def _parse_analysis_response(self, content: str) -> Dict[str, Any]:
        """解析分析响应"""
        import json
        import re

        # 提取JSON部分
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            data = json.loads(json_str)

            # 类型转换和验证
            data['complexity'] = float(data.get('complexity', 0.5))
            data['structured'] = float(data.get('structured', 0.5))
            data['needs_tools'] = bool(data.get('needs_tools', False))
            data['creativity'] = float(data.get('creativity', 0.5))
            data['certainty'] = float(data.get('certainty', 0.5))
            data['estimated_steps'] = int(data.get('estimated_steps', 3))
            data['domain'] = str(data.get('domain', 'general'))
            data['confidence'] = float(data.get('confidence', 0.5))

            return data
        else:
            raise ValueError("No JSON found in response")

    def _get_default_analysis(self, user_message: str) -> TaskAnalysis:
        """获取默认分析结果"""
        # 基于关键词的简单分析
        complexity = 0.3
        structured = 0.5
        needs_tools = False
        creativity = 0.4
        certainty = 0.6
        estimated_steps = 3
        domain = "general"

        # 复杂度分析
        if any(keyword in user_message for keyword in ["复杂", "高级", "系统", "架构"]):
            complexity = 0.8
        elif any(keyword in user_message for keyword in ["简单", "基础", "基本"]):
            complexity = 0.2

        # 结构化分析
        if any(keyword in user_message for keyword in ["步骤", "流程", "计划", "规划"]):
            structured = 0.8

        # 工具需求分析
        if any(keyword in user_message for keyword in ["API", "数据库", "工具", "调用"]):
            needs_tools = True

        # 领域分析
        if any(keyword in user_message for keyword in ["前端", "React", "页面"]):
            domain = "frontend"
        elif any(keyword in user_message for keyword in ["HTML", "网页"]):
            domain = "html"
        elif any(keyword in user_message for keyword in ["全栈", "后端", "API"]):
            domain = "fullstack"

        return TaskAnalysis(
            complexity=complexity,
            structured=structured,
            needs_tools=needs_tools,
            creativity=creativity,
            certainty=certainty,
            estimated_steps=estimated_steps,
            domain=domain,
            confidence=0.6
        )

    def get_strategy_recommendation(self, analysis: TaskAnalysis) -> str:
        """基于分析结果推荐策略"""
        # 决策逻辑
        if analysis.complexity > 0.7 and analysis.structured > 0.6:
            return "hybrid"  # 复杂且结构化 -> 混合策略
        elif analysis.structured > 0.7:
            return "plan_execute"  # 高度结构化 -> 计划执行
        elif analysis.needs_tools:
            return "react"  # 需要工具 -> ReAct
        elif analysis.creativity > 0.6:
            return "chain_of_thought"  # 高创造性 -> 思维链
        else:
            return "react"  # 默认使用ReAct