from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass
class TodoItem:
    """待办事项项"""
    id: str
    title: str
    description: str
    status: str = "pending"  # pending, in_progress, completed, cancelled
    priority: int = 1  # 1-5, 1为最高优先级
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    dependencies: List[str] = field(default_factory=list)
    estimated_time: Optional[int] = None  # 预估时间（分钟）
    actual_time: Optional[int] = None  # 实际耗时（分钟）
    tags: List[str] = field(default_factory=list)

class TodoManager:
    """TodoWrite任务管理器 - 提供显式的任务状态管理和约束"""

    def __init__(self):
        self.todos: Dict[str, TodoItem] = {}
        self.session_todos: Dict[str, List[str]] = {}  # session_id -> todo_ids

    def create_todo(self, session_id: str, title: str, description: str,
                   priority: int = 1, dependencies: List[str] = None,
                   estimated_time: int = None, tags: List[str] = None) -> str:
        """创建新的待办事项"""
        todo_id = str(uuid.uuid4())
        todo = TodoItem(
            id=todo_id,
            title=title,
            description=description,
            priority=priority,
            dependencies=dependencies or [],
            estimated_time=estimated_time,
            tags=tags or []
        )

        self.todos[todo_id] = todo

        # 关联到会话
        if session_id not in self.session_todos:
            self.session_todos[session_id] = []
        self.session_todos[session_id].append(todo_id)

        return todo_id

    def update_todo_status(self, todo_id: str, status: str) -> bool:
        """更新待办事项状态"""
        if todo_id not in self.todos:
            return False

        valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
        if status not in valid_statuses:
            return False

        self.todos[todo_id].status = status
        self.todos[todo_id].updated_at = datetime.now().isoformat()
        return True

    def update_todo_priority(self, todo_id: str, priority: int) -> bool:
        """更新待办事项优先级"""
        if todo_id not in self.todos or not (1 <= priority <= 5):
            return False

        self.todos[todo_id].priority = priority
        self.todos[todo_id].updated_at = datetime.now().isoformat()
        return True

    def delete_todo(self, todo_id: str) -> bool:
        """删除待办事项"""
        if todo_id not in self.todos:
            return False

        # 从会话中移除
        for session_id, todo_ids in self.session_todos.items():
            if todo_id in todo_ids:
                todo_ids.remove(todo_id)

        del self.todos[todo_id]
        return True

    def get_todo(self, todo_id: str) -> Optional[TodoItem]:
        """获取单个待办事项"""
        return self.todos.get(todo_id)
    def get_session_todos(self, session_id: str, status_filter: str = None) -> List[TodoItem]:
        """获取会话的所有待办事项"""
        if session_id not in self.session_todos:
            return []

        todo_ids = self.session_todos[session_id]
        todos = [self.todos[todo_id] for todo_id in todo_ids if todo_id in self.todos]

        if status_filter:
            todos = [todo for todo in todos if todo.status == status_filter]

        return sorted(todos, key=lambda x: (x.priority, x.created_at))

    def get_pending_dependencies(self, todo_id: str) -> List[TodoItem]:
        """获取待办事项的未完成依赖项"""
        todo = self.todos.get(todo_id)
        if not todo:
            return []

        dependencies = []
        for dep_id in todo.dependencies:
            dep_todo = self.todos.get(dep_id)
            if dep_todo and dep_todo.status != "completed":
                dependencies.append(dep_todo)

        return dependencies

    def can_start_todo(self, todo_id: str) -> bool:
        """检查是否可以开始待办事项（依赖是否满足）"""
        pending_deps = self.get_pending_dependencies(todo_id)
        return len(pending_deps) == 0

    def complete_todo(self, todo_id: str, actual_time: int = None) -> bool:
        """完成待办事项"""
        if not self.update_todo_status(todo_id, "completed"):
            return False

        if actual_time:
            self.todos[todo_id].actual_time = actual_time

        return True

    def get_todo_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取待办事项统计信息"""
        todos = self.get_session_todos(session_id)

        total = len(todos)
        completed = len([t for t in todos if t.status == "completed"])
        in_progress = len([t for t in todos if t.status == "in_progress"])
        pending = len([t for t in todos if t.status == "pending"])

        total_estimated_time = sum(t.estimated_time or 0 for t in todos)
        total_actual_time = sum(t.actual_time or 0 for t in todos if t.actual_time)

        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "completion_rate": completed / total if total > 0 else 0,
            "total_estimated_time": total_estimated_time,
            "total_actual_time": total_actual_time,
            "time_efficiency": total_estimated_time / total_actual_time if total_actual_time > 0 else 0
        }

    def export_todos(self, session_id: str) -> List[Dict[str, Any]]:
        """导出的待办事项列表"""
        todos = self.get_session_todos(session_id)
        return [
            {
                "id": todo.id,
                "title": todo.title,
                "description": todo.description,
                "status": todo.status,
                "priority": todo.priority,
                "created_at": todo.created_at,
                "updated_at": todo.updated_at,
                "dependencies": todo.dependencies,
                "estimated_time": todo.estimated_time,
                "actual_time": todo.actual_time,
                "tags": todo.tags
            }
            for todo in todos
        ]

    def import_todos(self, session_id: str, todos_data: List[Dict[str, Any]]) -> List[str]:
        """导入待办事项列表"""
        imported_ids = []

        for todo_data in todos_data:
            todo_id = self.create_todo(
                session_id=session_id,
                title=todo_data["title"],
                description=todo_data["description"],
                priority=todo_data.get("priority", 1),
                dependencies=todo_data.get("dependencies", []),
                estimated_time=todo_data.get("estimated_time"),
                tags=todo_data.get("tags", [])
            )
            imported_ids.append(todo_id)

            # 更新状态和时间
            if "status" in todo_data:
                self.update_todo_status(todo_id, todo_data["status"])

        return imported_ids

    def clear_session_todos(self, session_id: str) -> int:
        """清除会话的所有待办事项"""
        if session_id not in self.session_todos:
            return 0

        todo_ids = self.session_todos[session_id].copy()
        for todo_id in todo_ids:
            self.delete_todo(todo_id)

        del self.session_todos[session_id]
        return len(todo_ids)

# 创建全局TodoManager实例
todo_manager = TodoManager()