import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

class OperationStatus(Enum):
    """操作状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ProgressType(Enum):
    """进度类型枚举"""
    FILE_OPERATION = "file_operation"
    COMMAND_EXECUTION = "command_execution"
    PROJECT_ANALYSIS = "project_analysis"
    CODE_GENERATION = "code_generation"
    VALIDATION = "validation"

@dataclass
class StatusUpdate:
    """状态更新数据类"""
    operation_id: str
    status: OperationStatus
    progress_type: ProgressType
    message: str
    percentage: float = 0.0
    details: Dict[str, Any] = None
    timestamp: str = None
    error_message: str = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.details is None:
            self.details = {}
        if self.metadata is None:
            self.metadata = {}

class StatusFeedbackManager:
    """状态反馈管理器"""

    def __init__(self):
        self.operations: Dict[str, StatusUpdate] = {}
        self.callbacks: List[Callable[[StatusUpdate], None]] = []

    def create_operation(self, operation_id: str, progress_type: ProgressType,
                        initial_message: str = "操作开始") -> str:
        """
        创建新操作

        Args:
            operation_id: 操作ID
            progress_type: 进度类型
            initial_message: 初始消息

        Returns:
            操作ID
        """
        operation = StatusUpdate(
            operation_id=operation_id,
            status=OperationStatus.PENDING,
            progress_type=progress_type,
            message=initial_message
        )

        self.operations[operation_id] = operation
        self._notify_callbacks(operation)
        return operation_id

    def update_status(self, operation_id: str, status: OperationStatus,
                     message: str, percentage: float = None,
                     details: Dict[str, Any] = None,
                     error_message: str = None) -> bool:
        """
        更新操作状态

        Args:
            operation_id: 操作ID
            status: 新状态
            message: 状态消息
            percentage: 进度百分比 (0-100)
            details: 详细信息
            error_message: 错误消息

        Returns:
            是否成功更新
        """
        if operation_id not in self.operations:
            return False

        operation = self.operations[operation_id]
        operation.status = status
        operation.message = message

        if percentage is not None:
            operation.percentage = max(0.0, min(100.0, percentage))

        if details is not None:
            operation.details.update(details)

        if error_message is not None:
            operation.error_message = error_message

        operation.timestamp = datetime.now().isoformat()
        self._notify_callbacks(operation)
        return True

    def update_progress(self, operation_id: str, percentage: float,
                       message: str = None, details: Dict[str, Any] = None) -> bool:
        """
        更新操作进度

        Args:
            operation_id: 操作ID
            percentage: 进度百分比 (0-100)
            message: 进度消息
            details: 详细信息

        Returns:
            是否成功更新
        """
        if operation_id not in self.operations:
            return False

        operation = self.operations[operation_id]

        # 如果状态是pending，自动转换为running
        if operation.status == OperationStatus.PENDING:
            operation.status = OperationStatus.RUNNING

        operation.percentage = max(0.0, min(100.0, percentage))

        if message:
            operation.message = message

        if details:
            operation.details.update(details)

        operation.timestamp = datetime.now().isoformat()
        self._notify_callbacks(operation)
        return True

    def complete_operation(self, operation_id: str, message: str = "操作完成",
                          result_data: Dict[str, Any] = None) -> bool:
        """
        完成操作

        Args:
            operation_id: 操作ID
            message: 完成消息
            result_data: 结果数据

        Returns:
            是否成功完成
        """
        return self.update_status(
            operation_id=operation_id,
            status=OperationStatus.COMPLETED,
            message=message,
            percentage=100.0,
            details=result_data
        )

    def fail_operation(self, operation_id: str, error_message: str,
                      error_details: Dict[str, Any] = None) -> bool:
        """
        标记操作失败

        Args:
            operation_id: 操作ID
            error_message: 错误消息
            error_details: 错误详情

        Returns:
            是否成功标记失败
        """
        return self.update_status(
            operation_id=operation_id,
            status=OperationStatus.FAILED,
            message=f"操作失败: {error_message}",
            error_message=error_message,
            details=error_details
        )

    def cancel_operation(self, operation_id: str, message: str = "操作已取消") -> bool:
        """
        取消操作

        Args:
            operation_id: 操作ID
            message: 取消消息

        Returns:
            是否成功取消
        """
        return self.update_status(
            operation_id=operation_id,
            status=OperationStatus.CANCELLED,
            message=message
        )

    def get_operation_status(self, operation_id: str) -> Optional[StatusUpdate]:
        """
        获取操作状态

        Args:
            operation_id: 操作ID

        Returns:
            操作状态或None
        """
        return self.operations.get(operation_id)

    def get_all_operations(self) -> List[StatusUpdate]:
        """
        获取所有操作状态

        Returns:
            操作状态列表
        """
        return list(self.operations.values())

    def get_active_operations(self) -> List[StatusUpdate]:
        """
        获取活跃操作（未完成的操作）

        Returns:
            活跃操作列表
        """
        return [
            op for op in self.operations.values()
            if op.status in [OperationStatus.PENDING, OperationStatus.RUNNING]
        ]

    def clear_completed_operations(self, max_age_hours: int = 24) -> int:
        """
        清理已完成的操作

        Args:
            max_age_hours: 最大保留时间（小时）

        Returns:
            清理的操作数量
        """
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        removed_count = 0

        for operation_id in list(self.operations.keys()):
            operation = self.operations[operation_id]

            # 清理已完成且超过时间的操作
            if (operation.status in [OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELLED] and
                datetime.fromisoformat(operation.timestamp).timestamp() < cutoff_time):
                del self.operations[operation_id]
                removed_count += 1

        return removed_count

    def add_callback(self, callback: Callable[[StatusUpdate], None]) -> None:
        """
        添加状态更新回调

        Args:
            callback: 回调函数
        """
        self.callbacks.append(callback)

    def remove_callback(self, callback: Callable[[StatusUpdate], None]) -> bool:
        """
        移除状态更新回调

        Args:
            callback: 回调函数

        Returns:
            是否成功移除
        """
        try:
            self.callbacks.remove(callback)
            return True
        except ValueError:
            return False

    def _notify_callbacks(self, operation: StatusUpdate) -> None:
        """通知所有回调函数"""
        for callback in self.callbacks:
            try:
                callback(operation)
            except Exception as e:
                print(f"回调函数执行失败: {e}")

    def export_status_report(self) -> Dict[str, Any]:
        """
        导出状态报告

        Returns:
            状态报告
        """
        active_ops = self.get_active_operations()
        completed_ops = [
            op for op in self.operations.values()
            if op.status in [OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELLED]
        ]

        return {
            "timestamp": datetime.now().isoformat(),
            "total_operations": len(self.operations),
            "active_operations": len(active_ops),
            "completed_operations": len(completed_ops),
            "active_operations_list": [asdict(op) for op in active_ops],
            "recent_completed": [asdict(op) for op in completed_ops[-10:]]  # 最近10个完成的操作
        }

# 全局状态反馈管理器实例
status_manager = StatusFeedbackManager()

def create_file_operation_context(operation_id: str, file_path: str) -> StatusFeedbackManager:
    """
    创建文件操作状态上下文

    Args:
        operation_id: 操作ID
        file_path: 文件路径

    Returns:
        状态管理器
    """
    global status_manager
    status_manager.create_operation(
        operation_id=operation_id,
        progress_type=ProgressType.FILE_OPERATION,
        initial_message=f"开始处理文件: {file_path}"
    )
    return status_manager

def create_command_execution_context(operation_id: str, command: str) -> StatusFeedbackManager:
    """
    创建命令执行状态上下文

    Args:
        operation_id: 操作ID
        command: 命令

    Returns:
        状态管理器
    """
    global status_manager
    status_manager.create_operation(
        operation_id=operation_id,
        progress_type=ProgressType.COMMAND_EXECUTION,
        initial_message=f"开始执行命令: {command}"
    )
    return status_manager

def create_project_analysis_context(operation_id: str, project_path: str) -> StatusFeedbackManager:
    """
    创建项目分析状态上下文

    Args:
        operation_id: 操作ID
        project_path: 项目路径

    Returns:
        状态管理器
    """
    global status_manager
    status_manager.create_operation(
        operation_id=operation_id,
        progress_type=ProgressType.PROJECT_ANALYSIS,
        initial_message=f"开始分析项目: {project_path}"
    )
    return status_manager

def create_code_generation_context(operation_id: str, task_description: str) -> StatusFeedbackManager:
    """
    创建代码生成状态上下文

    Args:
        operation_id: 操作ID
        task_description: 任务描述

    Returns:
        状态管理器
    """
    global status_manager
    status_manager.create_operation(
        operation_id=operation_id,
        progress_type=ProgressType.CODE_GENERATION,
        initial_message=f"开始生成代码: {task_description}"
    )
    return status_manager

# 装饰器：自动管理操作状态
def with_status_feedback(progress_type: ProgressType, operation_name: str = None):
    """
    状态反馈装饰器

    Args:
        progress_type: 进度类型
        operation_name: 操作名称
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            global status_manager
            # 生成操作ID
            operation_id = f"{func.__name__}_{int(time.time() * 1000)}"

            # 创建操作
            operation_name_final = operation_name or func.__name__.replace('_', ' ').title()
            status_manager.create_operation(
                operation_id=operation_id,
                progress_type=progress_type,
                initial_message=f"开始{operation_name_final}"
            )

            try:
                # 更新为运行状态
                status_manager.update_status(
                    operation_id=operation_id,
                    status=OperationStatus.RUNNING,
                    message=f"正在{operation_name_final}",
                    percentage=10
                )

                # 执行函数
                result = func(*args, **kwargs)

                # 完成操作
                status_manager.complete_operation(
                    operation_id=operation_id,
                    message=f"{operation_name_final}完成",
                    result_data={"result": str(result)[:200] + "..." if len(str(result)) > 200 else str(result)}
                )

                return result

            except Exception as e:
                # 标记失败
                status_manager.fail_operation(
                    operation_id=operation_id,
                    error_message=str(e),
                    error_details={"exception_type": type(e).__name__}
                )
                raise

        return wrapper
    return decorator

# 工具函数：格式化状态信息供前端显示
def format_status_for_frontend(operation: StatusUpdate) -> Dict[str, Any]:
    """
    格式化状态信息供前端显示

    Args:
        operation: 操作状态

    Returns:
        格式化后的状态信息
    """
    status_colors = {
        OperationStatus.PENDING: "blue",
        OperationStatus.RUNNING: "orange",
        OperationStatus.COMPLETED: "green",
        OperationStatus.FAILED: "red",
        OperationStatus.CANCELLED: "gray"
    }

    status_icons = {
        OperationStatus.PENDING: "⏳",
        OperationStatus.RUNNING: "🔄",
        OperationStatus.COMPLETED: "✅",
        OperationStatus.FAILED: "❌",
        OperationStatus.CANCELLED: "⏹️"
    }

    return {
        "id": operation.operation_id,
        "status": operation.status.value,
        "status_display": {
            "text": operation.status.value.title(),
            "color": status_colors.get(operation.status, "gray"),
            "icon": status_icons.get(operation.status, "❓")
        },
        "type": operation.progress_type.value,
        "message": operation.message,
        "progress": {
            "percentage": operation.percentage,
            "text": f"{operation.percentage:.1f}%"
        },
        "timestamp": operation.timestamp,
        "has_error": operation.error_message is not None,
        "error_message": operation.error_message,
        "details": operation.details,
        "metadata": operation.metadata
    }