import pytest
import time
from datetime import datetime, timedelta
from app.tools.system.status_feedback import (
    StatusFeedbackManager, StatusUpdate, OperationStatus, ProgressType,
    status_manager, with_status_feedback, format_status_for_frontend
)

class TestStatusFeedback:
    def setup_method(self):
        """每个测试方法前重置状态管理器"""
        global status_manager
        status_manager = StatusFeedbackManager()

    def test_create_operation(self):
        """测试创建操作"""
        operation_id = status_manager.create_operation(
            "test_op_1",
            ProgressType.FILE_OPERATION,
            "测试操作"
        )

        assert operation_id == "test_op_1"
        assert "test_op_1" in status_manager.operations

        operation = status_manager.get_operation_status("test_op_1")
        assert operation.status == OperationStatus.PENDING
        assert operation.progress_type == ProgressType.FILE_OPERATION
        assert operation.message == "测试操作"

    def test_update_status(self):
        """测试更新状态"""
        status_manager.create_operation("test_op_2", ProgressType.COMMAND_EXECUTION)

        success = status_manager.update_status(
            "test_op_2",
            OperationStatus.RUNNING,
            "正在执行",
            percentage=50.0,
            details={"step": "processing"}
        )

        assert success is True

        operation = status_manager.get_operation_status("test_op_2")
        assert operation.status == OperationStatus.RUNNING
        assert operation.message == "正在执行"
        assert operation.percentage == 50.0
        assert operation.details["step"] == "processing"

    def test_update_progress(self):
        """测试更新进度"""
        status_manager.create_operation("test_op_3", ProgressType.PROJECT_ANALYSIS)

        # 更新进度应该自动将状态从PENDING改为RUNNING
        success = status_manager.update_progress(
            "test_op_3",
            percentage=75.0,
            message="分析中...",
            details={"files_processed": 10}
        )

        assert success is True

        operation = status_manager.get_operation_status("test_op_3")
        assert operation.status == OperationStatus.RUNNING
        assert operation.percentage == 75.0
        assert operation.message == "分析中..."
        assert operation.details["files_processed"] == 10

    def test_complete_operation(self):
        """测试完成操作"""
        status_manager.create_operation("test_op_4", ProgressType.CODE_GENERATION)

        success = status_manager.complete_operation(
            "test_op_4",
            "代码生成完成",
            {"files_created": 5, "lines_of_code": 200}
        )

        assert success is True

        operation = status_manager.get_operation_status("test_op_4")
        assert operation.status == OperationStatus.COMPLETED
        assert operation.message == "代码生成完成"
        assert operation.percentage == 100.0
        assert operation.details["files_created"] == 5
        assert operation.details["lines_of_code"] == 200

    def test_fail_operation(self):
        """测试失败操作"""
        status_manager.create_operation("test_op_5", ProgressType.VALIDATION)

        success = status_manager.fail_operation(
            "test_op_5",
            "验证失败",
            {"error_code": "VALIDATION_ERROR"}
        )

        assert success is True

        operation = status_manager.get_operation_status("test_op_5")
        assert operation.status == OperationStatus.FAILED
        assert "验证失败" in operation.message
        assert operation.error_message == "验证失败"
        assert operation.details["error_code"] == "VALIDATION_ERROR"

    def test_cancel_operation(self):
        """测试取消操作"""
        status_manager.create_operation("test_op_6", ProgressType.FILE_OPERATION)

        success = status_manager.cancel_operation("test_op_6", "用户取消")

        assert success is True

        operation = status_manager.get_operation_status("test_op_6")
        assert operation.status == OperationStatus.CANCELLED
        assert operation.message == "用户取消"

    def test_invalid_operation_id(self):
        """测试无效操作ID"""
        success = status_manager.update_status(
            "nonexistent_op",
            OperationStatus.RUNNING,
            "不应该成功"
        )

        assert success is False

    def test_get_all_operations(self):
        """测试获取所有操作"""
        status_manager.create_operation("op_1", ProgressType.FILE_OPERATION)
        status_manager.create_operation("op_2", ProgressType.COMMAND_EXECUTION)

        all_ops = status_manager.get_all_operations()
        assert len(all_ops) == 2

    def test_get_active_operations(self):
        """测试获取活跃操作"""
        status_manager.create_operation("active_op", ProgressType.FILE_OPERATION)
        status_manager.create_operation("completed_op", ProgressType.COMMAND_EXECUTION)

        # 完成一个操作
        status_manager.complete_operation("completed_op")

        active_ops = status_manager.get_active_operations()
        assert len(active_ops) == 1
        assert active_ops[0].operation_id == "active_op"

    def test_clear_completed_operations(self):
        """测试清理完成的操作"""
        # 创建一些操作
        status_manager.create_operation("old_op_1", ProgressType.FILE_OPERATION)
        status_manager.create_operation("old_op_2", ProgressType.COMMAND_EXECUTION)
        status_manager.create_operation("new_op", ProgressType.PROJECT_ANALYSIS)

        # 完成旧操作
        status_manager.complete_operation("old_op_1")
        status_manager.complete_operation("old_op_2")

        # 修改旧操作的时间戳（模拟过去的操作）
        old_time = (datetime.now() - timedelta(hours=25)).isoformat()
        status_manager.operations["old_op_1"].timestamp = old_time
        status_manager.operations["old_op_2"].timestamp = old_time

        # 清理24小时前的操作
        removed_count = status_manager.clear_completed_operations(max_age_hours=24)

        assert removed_count == 2
        assert len(status_manager.operations) == 1
        assert "new_op" in status_manager.operations

    def test_callback_functionality(self):
        """测试回调功能"""
        callback_called = []

        def test_callback(operation):
            callback_called.append(operation.operation_id)

        # 添加回调
        status_manager.add_callback(test_callback)

        # 创建操作（应该触发回调）
        status_manager.create_operation("callback_test", ProgressType.FILE_OPERATION)

        assert len(callback_called) == 1
        assert callback_called[0] == "callback_test"

        # 移除回调
        status_manager.remove_callback(test_callback)

        # 再次创建操作（不应该触发回调）
        callback_called.clear()
        status_manager.create_operation("callback_test_2", ProgressType.FILE_OPERATION)

        assert len(callback_called) == 0

    def test_export_status_report(self):
        """测试导出状态报告"""
        # 创建各种状态的操作
        status_manager.create_operation("pending_op", ProgressType.FILE_OPERATION)
        status_manager.create_operation("running_op", ProgressType.COMMAND_EXECUTION)
        status_manager.update_status("running_op", OperationStatus.RUNNING, "运行中", 50.0)

        status_manager.create_operation("completed_op", ProgressType.PROJECT_ANALYSIS)
        status_manager.complete_operation("completed_op", "已完成")

        report = status_manager.export_status_report()

        assert report["total_operations"] == 3
        assert report["active_operations"] == 2  # pending + running
        assert report["completed_operations"] == 1
        assert len(report["active_operations_list"]) == 2
        assert len(report["recent_completed"]) == 1

    def test_progress_percentage_limits(self):
        """测试进度百分比限制"""
        status_manager.create_operation("progress_test", ProgressType.FILE_OPERATION)

        # 测试超过100%
        status_manager.update_progress("progress_test", 150.0)
        operation = status_manager.get_operation_status("progress_test")
        assert operation.percentage == 100.0

        # 测试负数
        status_manager.update_progress("progress_test", -50.0)
        operation = status_manager.get_operation_status("progress_test")
        assert operation.percentage == 0.0

    def test_with_status_feedback_decorator(self):
        """测试状态反馈装饰器（简化测试）"""
        # 这个测试主要是验证装饰器不会抛出异常
        @with_status_feedback(ProgressType.CODE_GENERATION, "测试函数")
        def test_function(success=True):
            if not success:
                raise ValueError("测试错误")
            return "成功"

        # 测试成功情况 - 主要验证不会抛出异常
        result = test_function()
        assert result == "成功"

        # 测试失败情况 - 验证异常传播
        try:
            test_function(success=False)
            assert False, "应该抛出异常"
        except ValueError:
            pass  # 预期异常

    def test_format_status_for_frontend(self):
        """测试前端状态格式化"""
        status_manager.create_operation("frontend_test", ProgressType.FILE_OPERATION)
        status_manager.update_status(
            "frontend_test",
            OperationStatus.RUNNING,
            "正在处理文件",
            percentage=75.0,
            details={"file": "test.js"}
        )

        operation = status_manager.get_operation_status("frontend_test")
        formatted = format_status_for_frontend(operation)

        assert formatted["id"] == "frontend_test"
        assert formatted["status"] == "running"
        assert formatted["status_display"]["text"] == "Running"
        assert formatted["status_display"]["color"] == "orange"
        assert formatted["status_display"]["icon"] == "🔄"
        assert formatted["progress"]["percentage"] == 75.0
        assert formatted["progress"]["text"] == "75.0%"
        assert formatted["details"]["file"] == "test.js"

    def test_context_managers(self):
        """测试上下文管理器函数（简化测试）"""
        from app.tools.system.status_feedback import (
            create_file_operation_context,
            create_command_execution_context,
            create_project_analysis_context,
            create_code_generation_context
        )

        # 测试各种上下文创建函数 - 主要验证不会抛出异常
        try:
            file_context = create_file_operation_context("file_op", "test.js")
            command_context = create_command_execution_context("cmd_op", "npm install")
            project_context = create_project_analysis_context("proj_op", "/project")
            code_context = create_code_generation_context("code_op", "生成React组件")

            # 验证函数可以正常调用
            assert file_context is not None
            assert command_context is not None
            assert project_context is not None
            assert code_context is not None
        except Exception as e:
            assert False, f"上下文管理器函数应该正常工作，但出现了错误: {e}"

    def test_status_update_dataclass(self):
        """测试StatusUpdate数据类"""
        update = StatusUpdate(
            operation_id="test_update",
            status=OperationStatus.RUNNING,
            progress_type=ProgressType.FILE_OPERATION,
            message="测试更新",
            percentage=50.0
        )

        assert update.operation_id == "test_update"
        assert update.status == OperationStatus.RUNNING
        assert update.progress_type == ProgressType.FILE_OPERATION
        assert update.message == "测试更新"
        assert update.percentage == 50.0
        assert update.timestamp is not None
        assert update.details == {}
        assert update.metadata == {}
        assert update.error_message is None

    def test_operation_lifecycle(self):
        """测试操作生命周期"""
        op_id = "lifecycle_test"

        # 创建
        status_manager.create_operation(op_id, ProgressType.COMMAND_EXECUTION, "开始")
        op = status_manager.get_operation_status(op_id)
        assert op.status == OperationStatus.PENDING

        # 运行
        status_manager.update_status(op_id, OperationStatus.RUNNING, "运行中", 25.0)
        op = status_manager.get_operation_status(op_id)
        assert op.status == OperationStatus.RUNNING
        assert op.percentage == 25.0

        # 进度更新
        status_manager.update_progress(op_id, 75.0, "接近完成")
        op = status_manager.get_operation_status(op_id)
        assert op.status == OperationStatus.RUNNING
        assert op.percentage == 75.0

        # 完成
        status_manager.complete_operation(op_id, "完成", {"result": "success"})
        op = status_manager.get_operation_status(op_id)
        assert op.status == OperationStatus.COMPLETED
        assert op.percentage == 100.0
        assert op.details["result"] == "success"