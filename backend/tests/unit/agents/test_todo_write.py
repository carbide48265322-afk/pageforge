import pytest
from app.agents.tools.todo_manager import TodoManager
from app.agents.tools.todo_write_tool import TodoWriteTool

class TestTodoWrite:
    def test_todo_manager_basic_operations(self):
        """测试TodoManager基本操作"""
        manager = TodoManager()
        session_id = "test_session"

        # 创建任务
        todo_id = manager.create_todo(
            session_id=session_id,
            title="测试任务",
            description="这是一个测试任务",
            priority=1,
            estimated_time=30
        )

        assert todo_id is not None

        # 获取任务
        todo = manager.get_todo(todo_id)
        assert todo is not None
        assert todo.title == "测试任务"
        assert todo.status == "pending"

        # 更新任务状态
        result = manager.update_todo_status(todo_id, "in_progress")
        assert result is True

        todo = manager.get_todo(todo_id)
        assert todo.status == "in_progress"

        # 完成任务
        result = manager.complete_todo(todo_id, actual_time=25)
        assert result is True

        todo = manager.get_todo(todo_id)
        assert todo.status == "completed"
        assert todo.actual_time == 25

    def test_todo_write_tool(self):
        """测试TodoWrite工具"""
        tool = TodoWriteTool(session_id="test_session")

        # 创建任务
        result = tool.create_task.func(
            tool,
            title="工具测试任务",
            description="使用工具创建的测试任务",
            priority=2,
            estimated_time=45
        )

        assert "任务已创建" in result
        assert "ID:" in result

        # 获取任务列表
        result = tool.get_task_list.func(tool)
        assert "工具测试任务" in result
        assert "优先级: 2" in result

        # 获取统计信息
        result = tool.get_statistics.func(tool)
        assert "任务统计" in result
        assert "总任务数: 1" in result

    def test_task_dependencies(self):
        """测试任务依赖关系"""
        manager = TodoManager()
        session_id = "dependency_test"

        # 创建主任务
        main_task_id = manager.create_todo(
            session_id=session_id,
            title="主任务",
            description="需要依赖的任务",
            priority=1
        )

        # 创建依赖任务
        dep_task_id = manager.create_todo(
            session_id=session_id,
            title="依赖任务",
            description="前置任务",
            priority=1
        )

        # 更新主任务的依赖
        main_task = manager.get_todo(main_task_id)
        main_task.dependencies = [dep_task_id]

        # 检查是否可以开始主任务
        can_start = manager.can_start_todo(main_task_id)
        assert can_start is False

        # 完成依赖任务
        manager.complete_todo(dep_task_id)

        # 再次检查是否可以开始主任务
        can_start = manager.can_start_todo(main_task_id)
        assert can_start is True