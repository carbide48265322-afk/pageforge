"""设计子图 - 嵌入4个 CodeSubgraph 并行生成4套风格项目

并行执行机制:
使用 LangGraph 的 fan-out/fan-in 模式实现真正的并行执行:
1. 入口节点分发4个并行任务 (fan-out)
2. 4个 CodeSubgraph 同时执行 (通过 Send 机制)
3. 聚合节点等待所有任务完成 (fan-in)
"""
from typing import Dict, Any, List
import asyncio

try:
    from langgraph.graph import StateGraph, END
    from langgraph.types import interrupt, Send
except ImportError:
    StateGraph = Any
    END = None
    interrupt = lambda x: x
    Send = dict

from app.graph.subgraphs.base import BaseSubgraph
from app.graph.subgraphs.types import SubgraphMode
from app.graph.subgraphs.code import CodeSubgraph


class DesignSubgraph(BaseSubgraph[Dict]):
    """设计子图 - 嵌入4个 CodeSubgraph 并行生成4套风格项目
    
    流程:
    1. 并行执行4个 CodeSubgraph（每种风格一个）
       - 每个 CodeSubgraph 生成完整项目（api_spec + mock_data + frontend_code + style_code + extracted_homepage）
    2. 聚合4套完整项目
    3. 中断等待用户选择
    4. 输出选中的完整项目
    
    状态字段:
    - design_projects: 4套完整项目列表
    - selected_project: 用户选中的完整项目
    - selected_style: 选中的风格
    """
    
    mode = SubgraphMode.HIERARCHICAL
    
    # 4种预定义风格配置
    STYLES = [
        {
            "id": "modern",
            "name": "现代简约",
            "config": {
                "primary_color": "#1a1a1a",
                "secondary_color": "#f5f5f5",
                "font_family": "Inter, sans-serif",
                "spacing": "comfortable",
                "border_radius": "8px",
                "shadow": "subtle",
                "name": "现代简约"
            }
        },
        {
            "id": "tech",
            "name": "科技未来",
            "config": {
                "primary_color": "#00d4ff",
                "secondary_color": "#0a0a0a",
                "font_family": "JetBrains Mono, monospace",
                "spacing": "compact",
                "border_radius": "4px",
                "shadow": "glow",
                "effects": ["gradient", "blur"],
                "name": "科技未来"
            }
        },
        {
            "id": "business",
            "name": "商务专业",
            "config": {
                "primary_color": "#1e40af",
                "secondary_color": "#ffffff",
                "font_family": "Georgia, serif",
                "spacing": "spacious",
                "border_radius": "0px",
                "shadow": "none",
                "name": "商务专业"
            }
        },
        {
            "id": "creative",
            "name": "创意艺术",
            "config": {
                "primary_color": "#ff6b6b",
                "secondary_color": "#ffe66d",
                "font_family": "Playfair Display, serif",
                "spacing": "dynamic",
                "border_radius": "16px",
                "shadow": "colorful",
                "effects": ["animation", "pattern"],
                "name": "创意艺术"
            }
        },
    ]
    
    def __init__(self):
        super().__init__(
            config=type('Config', (), {
                'name': 'design',
                'subgraph_type': SubgraphMode.HIERARCHICAL,
                'mode': SubgraphMode.HIERARCHICAL,
                'max_iterations': 3,
                'enable_human_input': True,
                'enable_rollback': True
            })()
        )
        # 创建4个 CodeSubgraph 实例，每个绑定不同风格
        self.code_subgraphs = {
            style["id"]: CodeSubgraph(
                style_config=style["config"],
                output_prefix=f"{style['id']}_"
            )
            for style in self.STYLES
        }
    
    def build(self) -> StateGraph:
        """构建并行执行的 DesignSubgraph
        
        并行执行流程:
        1. dispatcher: 分发4个并行任务
        2. code_worker: 执行单个 CodeSubgraph (并行运行4个实例)
        3. aggregate: 等待所有4个任务完成，聚合结果
        4. select: 中断等待用户选择
        5. output: 输出选中的项目
        """
        builder = StateGraph(Dict)
        
        # 分发节点 - fan-out
        builder.add_node("dispatcher", self._dispatcher_node())
        
        # 工作节点 - 执行单个 CodeSubgraph
        builder.add_node("code_worker", self._code_worker_node())
        
        # 聚合节点 - fan-in
        builder.add_node("aggregate", self._aggregate_node())
        
        # 选择节点（中断点）
        builder.add_node("select", self._select_node())
        
        # 输出节点
        builder.add_node("output", self._output_node())
        
        # 边
        builder.set_entry_point("dispatcher")
        
        # dispatcher -> 并行发送4个 code_worker 任务
        builder.add_conditional_edges(
            "dispatcher",
            self._dispatch_workers,
            ["code_worker"]  # 所有 Send 都指向 code_worker
        )
        
        # code_worker -> aggregate (所有并行任务完成后)
        builder.add_edge("code_worker", "aggregate")
        
        builder.add_edge("aggregate", "select")
        
        # 选择后的条件边
        builder.add_conditional_edges(
            "select",
            self._route_after_select,
            {
                "confirm": "output",
                "regenerate": "dispatcher",  # 重新生成时回到 dispatcher
            }
        )
        
        builder.add_edge("output", END)
        
        return builder
    
    def _dispatcher_node(self):
        """分发节点 - 初始化并行任务跟踪"""
        async def dispatcher(state: Dict) -> Dict:
            """初始化并行执行状态"""
            return {
                "design_parallel_jobs": [],  # 跟踪并行任务
                "design_completed_jobs": [],  # 已完成任务
                "design_start_time": None,  # 开始时间
            }
        return dispatcher
    
    def _dispatch_workers(self, state: Dict) -> List[Send]:
        """分发4个并行 CodeSubgraph 任务
        
        使用 LangGraph Send 机制实现真正的并行执行。
        返回4个 Send 对象，每个对应一个风格的 CodeSubgraph。
        """
        sends = []
        for style in self.STYLES:
            style_id = style["id"]
            sends.append(
                Send(
                    "code_worker",
                    {
                        "style_id": style_id,
                        "style_config": style["config"],
                        # 传递主状态的关键字段
                        "requirements_doc": state.get("requirements_doc", ""),
                        "project_idea": state.get("project_idea", ""),
                        "features": state.get("features", []),
                    }
                )
            )
        return sends
    
    def _code_worker_node(self):
        """工作节点 - 执行单个 CodeSubgraph
        
        每个并行实例执行自己的 CodeSubgraph，
        结果写入带前缀的状态字段。
        """
        async def code_worker(state: Dict) -> Dict:
            """执行单个 CodeSubgraph"""
            style_id = state.get("style_id")
            
            if not style_id or style_id not in self.code_subgraphs:
                return {"error": f"Unknown style_id: {style_id}"}
            
            # 获取对应的 CodeSubgraph 实例
            code_subgraph = self.code_subgraphs[style_id]
            
            # 构建子图
            subgraph = code_subgraph.get_graph()
            
            # 准备子图输入状态
            subgraph_input = {
                **state,  # 包含 style_id, style_config, requirements_doc 等
                "current_phase": f"code_{style_id}",
            }
            
            # 执行子图
            try:
                result = await subgraph.ainvoke(subgraph_input)
                
                # 提取带前缀的结果字段
                prefix = f"{style_id}_"
                output_keys = [
                    "api_spec", "mock_data", "frontend_code", 
                    "style_code", "extracted_homepage"
                ]
                
                output = {
                    "completed_job": {
                        "style_id": style_id,
                        "status": "success"
                    }
                }
                
                # 将子图结果复制到主状态（带前缀）
                for key in output_keys:
                    prefixed_key = f"{prefix}{key}"
                    if prefixed_key in result:
                        output[prefixed_key] = result[prefixed_key]
                
                return output
                
            except Exception as e:
                return {
                    "completed_job": {
                        "style_id": style_id,
                        "status": "error",
                        "error": str(e)
                    }
                }
        
        return code_worker
    
    def _aggregate_node(self):
        """聚合节点 - 收集4个 CodeSubgraph 的输出 (fan-in)
        
        LangGraph 保证所有并行 code_worker 完成后才会执行此节点。
        """
        async def aggregate(state: Dict) -> Dict:
            """聚合4套完整项目"""
            projects = []
            completed_jobs = state.get("completed_jobs", [])
            
            for style in self.STYLES:
                style_id = style["id"]
                prefix = f"{style_id}_"
                
                # 从状态中获取该 CodeSubgraph 的输出
                project = {
                    "style_id": style_id,
                    "style_name": style["name"],
                    "style_config": style["config"],
                    "api_spec": state.get(f"{prefix}api_spec", {}),
                    "mock_data": state.get(f"{prefix}mock_data", {}),
                    "frontend_code": state.get(f"{prefix}frontend_code", {}),
                    "style_code": state.get(f"{prefix}style_code", {}),
                    "extracted_homepage": state.get(f"{prefix}extracted_homepage", ""),
                    "status": "success" if state.get(f"{prefix}api_spec") else "pending"
                }
                projects.append(project)
            
            # 检查是否有失败的任务
            failed_jobs = [p for p in projects if p["status"] != "success"]
            
            return {
                "design_projects": projects,
                "design_aggregate_count": len(projects),
                "design_success_count": len([p for p in projects if p["status"] == "success"]),
                "design_failed_count": len(failed_jobs),
                "design_failed_styles": [p["style_id"] for p in failed_jobs],
            }
        
        return aggregate
    
    def _select_node(self):
        """选择节点 - 中断等待用户选择"""
        async def select(state: Dict) -> Dict:
            """构建选择表单并中断"""
            projects = state.get("design_projects", [])
            
            # 构建选择选项（展示首页预览）
            options = [
                {
                    "id": p["style_id"],
                    "name": p["style_name"],
                    "homepage_preview": p["extracted_homepage"][:1000] if p["extracted_homepage"] else "",
                    "style_preview": p["style_config"]
                }
                for p in projects
            ]
            
            # 构建 Schema
            schema = {
                "type": "object",
                "title": "请选择设计方案",
                "description": "从4种风格中选择您喜欢的设计",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["confirm", "regenerate"],
                        "title": "操作"
                    },
                    "selected_style": {
                        "type": "string",
                        "enum": [p["style_id"] for p in projects],
                        "title": "选择风格"
                    },
                    "feedback": {
                        "type": "string",
                        "title": "修改建议"
                    }
                },
                "required": ["action", "selected_style"]
            }
            
            # 中断等待用户选择
            try:
                result = interrupt({
                    "schema": schema,
                    "context": {
                        "projects": projects,
                        "options": options
                    }
                })
            except Exception:
                # Mock interrupt for testing
                result = {"action": "confirm", "selected_style": "modern"}
            
            return {
                "human_input_response": result,
                "selected_style_id": result.get("selected_style")
            }
        
        return select
    
    def _output_node(self):
        """输出节点 - 输出选中的完整项目"""
        async def output(state: Dict) -> Dict:
            """输出选中的完整项目"""
            projects = state.get("design_projects", [])
            selected_id = state.get("selected_style_id")
            
            # 找到选中的项目
            selected_project = None
            for p in projects:
                if p["style_id"] == selected_id:
                    selected_project = p
                    break
            
            if not selected_project:
                selected_project = projects[0] if projects else {}
            
            # 将选中的项目数据提升到主状态
            return {
                "selected_design": selected_project,
                "design_style": selected_project.get("style_config", {}),
                "api_spec": selected_project.get("api_spec", {}),
                "mock_data": selected_project.get("mock_data", {}),
                "frontend_code": selected_project.get("frontend_code", {}),
                "style_code": selected_project.get("style_code", {}),
                "extracted_homepage": selected_project.get("extracted_homepage", ""),
                "current_phase": "delivery",
                "phase_status": "completed"
            }
        
        return output
    
    def _route_after_select(self, state: Dict) -> str:
        """选择后的路由"""
        response = state.get("human_input_response", {})
        action = response.get("action", "confirm")
        return "confirm" if action == "confirm" else "regenerate"
    
    async def on_enter(self, state: Dict) -> Dict:
        """进入子图初始化"""
        state["current_phase"] = "design"
        state["phase_status"] = "running"
        state["phase"] = "design"  # [DEPRECATED] 向后兼容
        return state
    
    async def on_exit(self, state: Dict) -> Dict:
        """离开子图保存快照"""
        from datetime import datetime
        state["design_snapshot"] = {
            "confirmed": True,
            "selected_style": state.get("selected_style_id"),
            "projects_count": state.get("design_aggregate_count", 0),
            "confirmed_at": datetime.now().isoformat()
        }
        return state
