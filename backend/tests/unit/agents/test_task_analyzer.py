import pytest
from app.agents.task_analyzer import TaskAnalyzer, TaskAnalysis

class TestTaskAnalyzer:
    def test_default_analysis(self):
        """测试默认任务分析"""
        analyzer = TaskAnalyzer()

        # 测试前端任务默认分析
        frontend_task = "创建一个React博客网站，需要文章列表和详情页"
        analysis = analyzer._get_default_analysis(frontend_task)

        assert isinstance(analysis, TaskAnalysis)
        assert 0 <= analysis.complexity <= 1
        assert 0 <= analysis.structured <= 1
        assert isinstance(analysis.needs_tools, bool)
        assert analysis.domain in ["frontend", "html", "fullstack", "general"]

    def test_strategy_recommendation(self):
        """测试策略推荐"""
        analyzer = TaskAnalyzer()

        # 测试结构化任务 -> Plan-and-Execute
        structured_analysis = TaskAnalysis(
            complexity=0.6,
            structured=0.8,
            needs_tools=False,
            creativity=0.3,
            certainty=0.9,
            estimated_steps=5,
            domain="frontend",
            confidence=0.8
        )

        strategy = analyzer.get_strategy_recommendation(structured_analysis)
        assert strategy == "plan_execute"

        # 测试工具需求任务 -> ReAct
        tools_analysis = TaskAnalysis(
            complexity=0.5,
            structured=0.4,
            needs_tools=True,
            creativity=0.3,
            certainty=0.6,
            estimated_steps=3,
            domain="fullstack",
            confidence=0.7
        )

        strategy = analyzer.get_strategy_recommendation(tools_analysis)
        assert strategy == "react"