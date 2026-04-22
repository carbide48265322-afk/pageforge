"""FeatureSubgraph - 功能选择子图

基于 SelectionSubgraph 实现：
1. 选择模式：Demo演示版 / 完整项目版
2. 展示功能清单
3. 用户勾选需要的功能
4. 确认功能范围
"""

from typing import Any, Dict, List, Union
from datetime import datetime

from app.graph.state import AgentState
from .selection import SelectionSubgraph, Option, SelectionResult, SelectionMode


class FeatureSubgraph(SelectionSubgraph):
    """功能选择子图
    
    实现功能清单选择和确认流程。
    """
    
    name = "feature"
    description = "功能范围选择"
    selection_mode = SelectionMode.SINGLE  # 先选择模式（Demo/完整）
    
    # 预定义功能清单
    feature_catalog = {
        "demo": {
            "mode": "demo",
            "name": "演示版",
            "description": "快速生成交互演示，适合验证想法",
            "estimated_time": "5-10分钟",
            "features": [
                {"id": "basic_ui", "name": "基础UI界面", "default": True, "description": "响应式页面布局"},
                {"id": "core_function", "name": "核心功能演示", "default": True, "description": "主要交互流程"},
                {"id": "responsive", "name": "响应式布局", "default": True, "description": "适配移动端"},
            ]
        },
        "full": {
            "mode": "full",
            "name": "完整项目版",
            "description": "生产级完整应用，包含前后端",
            "estimated_time": "30-60分钟",
            "features": [
                {"id": "user_system", "name": "用户系统（登录/注册）", "default": True, "description": "JWT认证、用户管理"},
                {"id": "database", "name": "数据库集成", "default": True, "description": "数据持久化"},
                {"id": "api_backend", "name": "后端API", "default": True, "description": "RESTful API"},
                {"id": "admin_panel", "name": "管理后台", "default": False, "description": "内容管理界面"},
                {"id": "file_upload", "name": "文件上传", "default": False, "description": "图片/文档上传"},
                {"id": "search_filter", "name": "搜索过滤", "default": False, "description": "全文搜索、筛选"},
                {"id": "notification", "name": "消息通知", "default": False, "description": "站内信/邮件通知"},
                {"id": "analytics", "name": "数据统计", "default": False, "description": "访问统计、报表"},
                {"id": "deployment", "name": "部署配置", "default": False, "description": "Docker、CI/CD配置"},
            ]
        }
    }
    
    def get_options(self, state: AgentState) -> List[Union[Option, Dict]]:
        """获取功能选项
        
        Args:
            state: 当前状态
            
        Returns:
            List[Option]: 功能选项列表
        """
        return [
            Option(
                id="demo",
                title="演示版",
                description="快速生成交互演示，适合验证想法（5-10分钟）",
                metadata={"catalog": self.feature_catalog["demo"]}
            ),
            Option(
                id="full",
                title="完整项目版",
                description="生产级完整应用，包含前后端（30-60分钟）",
                metadata={"catalog": self.feature_catalog["full"]}
            )
        ]
    
    def _validate_node(self, state: AgentState) -> Dict:
        """验证选择并处理功能清单
        
        Args:
            state: 当前状态
            
        Returns:
            Dict: 状态更新
        """
        subgraph_state = self._get_subgraph_state(state)
        
        selection_data = subgraph_state.get(self._selection_key, {})
        options = subgraph_state.get(self._options_key, [])
        
        # 提取选择的模式
        selected_ids = selection_data.get("selected_ids", [])
        if isinstance(selected_ids, str):
            selected_ids = [selected_ids]
        
        if not selected_ids:
            subgraph_state[self._status_key] = "validation_failed"
            return {self.get_state_key(): subgraph_state}
        
        selected_mode = selected_ids[0]  # 单选
        
        # 获取该模式的功能清单
        catalog = self.feature_catalog.get(selected_mode, {})
        default_features = [f["id"] for f in catalog.get("features", []) if f.get("default", False)]
        all_features = [f["id"] for f in catalog.get("features", [])]
        
        # 创建结果
        result = SelectionResult(
            selected_ids=selected_ids,
            selected_options=[opt for opt in options if opt.id in selected_ids],
            mode=self.selection_mode,
            timestamp=datetime.now()
        )
        
        subgraph_state[self._result_key] = result
        subgraph_state[self._status_key] = "completed"
        
        # 更新主状态
        from datetime import datetime
        now = datetime.now().isoformat()
        history = state.get("phase_history", [])
        return {
            self.get_state_key(): subgraph_state,
            "project_mode": selected_mode,
            "selected_features": default_features,
            "available_features": all_features,
            "feature_approved": True,
            "current_phase": "code",
            "phase": "code",  # [DEPRECATED] 向后兼容
            "phase_status": "running",
            "feature_snapshot": {
                "confirmed": True,
                "project_mode": selected_mode,
                "selected_features": default_features,
                "all_features": all_features,
                "confirmed_at": now,
            },
            "phase_history": history + [{
                "from_phase": "feature",
                "to_phase": "code",
                "trigger": "user_confirmed",
                "timestamp": now,
            }],
        }
