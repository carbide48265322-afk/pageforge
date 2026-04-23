from typing import Dict, List, Optional, Any
from langchain_core.tools import tool
from langchain_core.callbacks import CallbackManagerForToolRun
from .todo_manager import todo_manager, TodoItem

class TodoWriteTool:
    """TodoWrite工具 - 为Agent提供任务管理约束"""

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id

    @tool
    def create_task(self, title: str, description: str, priority: int = 1,
                   dependencies: List[str] = None, estimated_time: int = None,
                   tags: List[str] = None) -> str:
        """创建新的任务项

        Args:
            title: 任务标题
            description: 任务描述
            priority: 优先级 (1-5, 1为最高)
            dependencies: 依赖的任务ID列表
            estimated_time: 预估时间（分钟）
            tags: 标签列表

        Returns:
            任务ID
        """
        todo_id = todo_manager.create_todo(
            session_id=self.session_id,
            title=title,
            description=description,
            priority=priority,
            dependencies=dependencies or [],
            estimated_time=estimated_time,
            tags=tags or []
        )
        return f"任务已创建，ID: {todo_id}"

    @tool
    def update_task_status(self, todo_id: str, status: str) -> str:
        """更新任务状态

        Args:
            todo_id: 任务ID
            status: 新状态 (pending, in_progress, completed, cancelled)

        Returns:
            操作结果
        """
        valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
        if status not in valid_statuses:
            return f"无效状态。可用状态: {', '.join(valid_statuses)}"

        if todo_manager.update_todo_status(todo_id, status):
            return f"任务 {todo_id} 状态已更新为 {status}"
        else:
            return f"任务 {todo_id} 不存在"

    @tool
    def complete_task(self, todo_id: str, actual_time: int = None) -> str:
        """完成任务

        Args:
            todo_id: 任务ID
            actual_time: 实际耗时（分钟）

        Returns:
            操作结果
        """
        if not todo_manager.can_start_todo(todo_id):
            pending_deps = todo_manager.get_pending_dependencies(todo_id)
            dep_titles = [dep.title for dep in pending_deps]
            return f"无法完成任务，存在未完成的依赖项: {', '.join(dep_titles)}"

        if todo_manager.complete_todo(todo_id, actual_time):
            return f"任务 {todo_id} 已完成"
        else:
            return f"任务 {todo_id} 不存在"

    @tool
    def get_task_list(self, status_filter: str = None) -> str:
        """获取任务列表

        Args:
            status_filter: 状态过滤器 (pending, in_progress, completed, cancelled)

        Returns:
            任务列表信息
        """
        todos = todo_manager.get_session_todos(self.session_id, status_filter)

        if not todos:
            return "暂无任务"

        result = []
        for todo in todos:
            deps_info = f" (依赖: {', '.join(todo.dependencies)})" if todo.dependencies else ""
            time_info = f" [预估: {todo.estimated_time}分钟]" if todo.estimated_time else ""
            result.append(
                f"ID: {todo.id}\n"
                f"标题: {todo.title}\n"
                f"状态: {todo.status}\n"
                f"优先级: {todo.priority}\n"
                f"描述: {todo.description}{deps_info}{time_info}"
            )

        return "\n\n".join(result)

    @tool
    def get_task_details(self, todo_id: str) -> str:
        """获取任务详情

        Args:
            todo_id: 任务ID

        Returns:
            任务详细信息
        """
        todo = todo_manager.get_todo(todo_id)
        if not todo:
            return f"任务 {todo_id} 不存在"

        deps_info = f"\n依赖任务: {', '.join(todo.dependencies)}" if todo.dependencies else ""
        tags_info = f"\n标签: {', '.join(todo.tags)}" if todo.tags else ""
        time_info = ""
        if todo.estimated_time:
            time_info += f"\n预估时间: {todo.estimated_time}分钟"
        if todo.actual_time:
            time_info += f"\n实际时间: {todo.actual_time}分钟"

        return (
            f"任务ID: {todo.id}\n"
            f"标题: {todo.title}\n"
            f"描述: {todo.description}\n"
            f"状态: {todo.status}\n"
            f"优先级: {todo.priority}\n"
            f"创建时间: {todo.created_at}\n"
            f"更新时间: {todo.updated_at}{deps_info}{tags_info}{time_info}"
        )

    @tool
    def delete_task(self, todo_id: str) -> str:
        """删除任务

        Args:
            todo_id: 任务ID

        Returns:
            操作结果
        """
        if todo_manager.delete_todo(todo_id):
            return f"任务 {todo_id} 已删除"
        else:
            return f"任务 {todo_id} 不存在"

    @tool
    def get_statistics(self) -> str:
        """获取任务统计信息

        Returns:
            统计信息
        """
        stats = todo_manager.get_todo_statistics(self.session_id)

        return (
            f"任务统计:\n"
            f"总任务数: {stats['total']}\n"
            f"已完成: {stats['completed']}\n"
            f"进行中: {stats['in_progress']}\n"
            f"待处理: {stats['pending']}\n"
            f"完成率: {stats['completion_rate']:.1%}\n"
            f"预估总时间: {stats['total_estimated_time']}分钟\n"
            f"实际总时间: {stats['total_actual_time']}分钟\n"
            f"时间效率: {stats['time_efficiency']:.2f}"
        )

    @tool
    def can_start_task(self, todo_id: str) -> str:
        """检查是否可以开始任务

        Args:
            todo_id: 任务ID

        Returns:
            检查结果
        """
        if todo_manager.can_start_todo(todo_id):
            return f"任务 {todo_id} 可以开始"
        else:
            pending_deps = todo_manager.get_pending_dependencies(todo_id)
            dep_titles = [dep.title for dep in pending_deps]
            return f"任务 {todo_id} 无法开始，存在未完成的依赖项: {', '.join(dep_titles)}"

    def get_all_tools(self):
        """获取所有工具函数"""
        return [
            self.create_task,
            self.update_task_status,
            self.complete_task,
            self.get_task_list,
            self.get_task_details,
            self.delete_task,
            self.get_statistics,
            self.can_start_task
        ]

# 创建默认工具实例
todo_write_tool = TodoWriteTool()