from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.agents.unified_agent import UnifiedAgent
from app.graph.state import AgentState

router = APIRouter(prefix="/unified-agent", tags=["unified-agent"])

# 创建全局Agent实例
unified_agent = UnifiedAgent()

@router.post("/process")
async def process_with_unified_agent(request: Dict[str, Any]):
    """使用统一Agent处理请求"""
    try:
        user_message = request.get("message", "")
        session_id = request.get("session_id", "default")

        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")

        # 初始化状态
        initial_state = AgentState(
            user_message=user_message,
            session_id=session_id,
            base_html="",
            task_list=[],
            current_html="",
            validation_errors=[],
            iteration_count=0,
            fix_count=0,
            response_message="",
            output_html="",
            output_version=0,
            is_complete=False
        )

        # 使用统一Agent处理
        result = await unified_agent.process(initial_state)

        return {
            "success": True,
            "message": result.get("response_message", ""),
            "strategy_used": result.get("strategy_info", {}).get("name", "unknown"),
            "task_analysis": result.get("task_analysis", {}),
            "result": result.get("result", {}),
            "execution_metadata": result.get("execution_metadata", {})
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategies")
async def get_available_strategies():
    """获取可用策略列表"""
    strategies_info = {}

    for name, strategy in unified_agent.strategies.items():
        strategies_info[name] = {
            "name": name,
            "description": strategy.get_description(),
            "available": True
        }

    return {
        "strategies": strategies_info,
        "total_count": len(strategies_info)
    }

@router.get("/performance")
async def get_strategy_performance():
    """获取策略性能报告"""
    report = unified_agent.get_strategy_performance_report()

    return {
        "success": True,
        "performance_report": report,
        "total_strategies": len(report)
    }

@router.post("/strategy/{strategy_name}")
async def execute_with_specific_strategy(strategy_name: str, request: Dict[str, Any]):
    """使用指定策略执行任务"""
    try:
        user_message = request.get("message", "")
        session_id = request.get("session_id", "default")

        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")

        if strategy_name not in unified_agent.strategies:
            raise HTTPException(status_code=404, detail=f"Strategy '{strategy_name}' not found")

        # 初始化状态
        initial_state = AgentState(
            user_message=user_message,
            session_id=session_id,
            base_html="",
            task_list=[],
            current_html="",
            validation_errors=[],
            iteration_count=0,
            fix_count=0,
            response_message="",
            output_html="",
            output_version=0,
            is_complete=False
        )

        # 分析任务
        task_analysis = await unified_agent.task_analyzer.analyze_task(user_message)

        # 使用指定策略
        strategy = unified_agent.strategies[strategy_name]
        if not strategy.can_handle(task_analysis):
            raise HTTPException(status_code=400, detail=f"Strategy '{strategy_name}' cannot handle this task")

        result = await strategy.execute(initial_state, task_analysis)

        return {
            "success": True,
            "strategy_used": strategy_name,
            "result": result.get("result", {}),
            "task_analysis": {
                "complexity": task_analysis.complexity,
                "structured": task_analysis.structured,
                "domain": task_analysis.domain
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))