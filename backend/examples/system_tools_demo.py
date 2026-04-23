#!/usr/bin/env python3
"""
系统工具演示脚本
展示PageForge系统工具的使用方法
"""

import os
import tempfile
from app.tools.system.file_operations import save_generated_code, read_project_file, create_project_structure
from app.tools.system.command_execution import execute_npm_command, execute_shell_command
from app.tools.system.project_monitor import get_project_status, analyze_project_structure
from app.tools.system.status_feedback import (
    status_manager, ProgressType, OperationStatus,
    create_file_operation_context, create_command_execution_context
)
from app.tools.system.config import system_config

def demo_file_operations():
    """演示文件操作工具"""
    print("\n=== 文件操作工具演示 ===")

    # 创建临时项目目录用于演示
    with tempfile.TemporaryDirectory() as tmpdir:
        old_root = system_config.project_root
        system_config.project_root = tmpdir

        try:
            # 1. 保存生成的代码
            print("1. 保存生成的代码文件...")
            result = save_generated_code.invoke({
                "file_path": "src/components/Header.js",
                "code_content": """import React from 'react';

const Header = () => {
  return (
    <header className="app-header">
      <h1>PageForge 项目</h1>
    </header>
  );
};

export default Header;""",
                "file_type": "javascript"
            })

            if result["success"]:
                print(f"✅ 文件保存成功: {result['saved_path']}")
                print(f"   文件大小: {result['file_size']} 字节")
                print(f"   验证结果: {result['validation']}")
            else:
                print(f"❌ 文件保存失败: {result['error']}")

            # 2. 读取项目文件
            print("\n2. 读取项目文件...")
            read_result = read_project_file.invoke({"file_path": "src/components/Header.js"})

            if read_result["success"]:
                print(f"✅ 文件读取成功")
                print(f"   文件大小: {read_result['size']} 字节")
                print(f"   是否为文本文件: {read_result['is_text_file']}")
                print(f"   内容预览: {read_result['content'][:50]}...")
            else:
                print(f"❌ 文件读取失败: {read_result['error']}")

            # 3. 创建项目结构
            print("\n3. 创建项目结构...")
            structure = {
                "src": {
                    "components": ["Footer.js", "Sidebar.js"],
                    "styles": ["main.css", "variables.css"],
                    "utils": ["helpers.js"]
                },
                "public": ["index.html", "favicon.ico"],
                "tests": ["unit", "integration"]
            }

            structure_result = create_project_structure.invoke({"structure": structure})

            if structure_result["success"]:
                print(f"✅ 项目结构创建成功")
                print(f"   创建的文件数: {len(structure_result['created_files'])}")
                print(f"   创建的目录数: {len(structure_result['created_dirs'])}")
                print(f"   文件列表: {structure_result['created_files'][:5]}...")
            else:
                print(f"❌ 项目结构创建失败: {structure_result['error']}")

        finally:
            system_config.project_root = old_root

def demo_command_execution():
    """演示命令执行工具"""
    print("\n=== 命令执行工具演示 ===")

    # 1. 执行npm命令（模拟）
    print("1. 执行npm命令...")
    try:
        # 注意：这里会实际执行命令，所以使用安全的命令
        result = execute_shell_command.invoke({
            "command": "echo",
            "args": ["Hello from PageForge!"],
            "timeout": 10
        })

        if result["success"]:
            print(f"✅ 命令执行成功")
            print(f"   退出码: {result['exit_code']}")
            print(f"   输出: {result['stdout']}")
            print(f"   执行时间: {result['duration']:.2f}秒")
        else:
            print(f"❌ 命令执行失败: {result.get('error', '未知错误')}")

    except Exception as e:
        print(f"❌ 命令执行异常: {e}")

def demo_project_monitoring():
    """演示项目监控工具"""
    print("\n=== 项目监控工具演示 ===")

    # 创建临时项目用于演示
    with tempfile.TemporaryDirectory() as tmpdir:
        old_root = system_config.project_root
        system_config.project_root = tmpdir

        try:
            # 创建一些测试文件
            os.makedirs(os.path.join(tmpdir, "src"), exist_ok=True)
            with open(os.path.join(tmpdir, "package.json"), 'w') as f:
                f.write('{"name": "demo-project", "version": "1.0.0"}')
            with open(os.path.join(tmpdir, "src", "index.js"), 'w') as f:
                f.write('console.log("Hello World");')

            # 1. 获取项目状态
            print("1. 获取项目状态...")
            status_result = get_project_status.invoke({"project_path": "."})

            if status_result["success"]:
                print(f"✅ 项目状态获取成功")
                print(f"   是否为目录: {status_result['is_directory']}")
                print(f"   项目统计: {status_result.get('directory_info', {})}")
            else:
                print(f"❌ 项目状态获取失败: {status_result['error']}")

            # 2. 分析项目结构
            print("\n2. 分析项目结构...")
            analysis_result = analyze_project_structure.invoke({"root_directory": "."})

            if analysis_result["success"]:
                print(f"✅ 项目结构分析成功")
                summary = analysis_result["summary"]
                print(f"   总文件数: {summary['total_files']}")
                print(f"   总目录数: {summary['total_directories']}")
                print(f"   总大小: {summary['total_size_human']}")
                print(f"   文件类型分布: {summary['file_types']}")
            else:
                print(f"❌ 项目结构分析失败: {analysis_result['error']}")

        finally:
            system_config.project_root = old_root

def demo_status_feedback():
    """演示状态反馈系统"""
    print("\n=== 状态反馈系统演示 ===")

    # 重置状态管理器
    global status_manager
    from app.tools.system.status_feedback import StatusFeedbackManager
    status_manager = StatusFeedbackManager()

    # 1. 创建操作
    print("1. 创建文件操作...")
    op_id = status_manager.create_operation(
        "demo_file_op",
        ProgressType.FILE_OPERATION,
        "演示文件操作"
    )
    print(f"   操作ID: {op_id}")

    # 2. 更新进度
    print("\n2. 更新操作进度...")
    status_manager.update_progress(op_id, 25.0, "正在处理文件...")
    status_manager.update_progress(op_id, 50.0, "文件处理中...")
    status_manager.update_progress(op_id, 75.0, "即将完成...")

    # 3. 完成操作
    print("\n3. 完成操作...")
    status_manager.complete_operation(
        op_id,
        "文件操作完成",
        {"files_processed": 1, "total_size": 1024}
    )

    # 4. 查看状态报告
    print("\n4. 生成状态报告...")
    report = status_manager.export_status_report()
    print(f"   总操作数: {report['total_operations']}")
    print(f"   活跃操作: {report['active_operations']}")
    print(f"   已完成操作: {report['completed_operations']}")

    # 5. 演示上下文管理器
    print("\n5. 使用上下文管理器...")
    ctx = create_file_operation_context("demo_context", "example.js")
    print(f"   上下文管理器类型: {type(ctx)}")

def main():
    """主演示函数"""
    print("🚀 PageForge 系统工具演示")
    print("=" * 50)

    # 演示各个模块
    demo_file_operations()
    demo_command_execution()
    demo_project_monitoring()
    demo_status_feedback()

    print("\n" + "=" * 50)
    print("✅ 演示完成！所有系统工具都已成功展示。")
    print("\n主要功能包括：")
    print("• 🔒 安全验证：路径和命令安全检查")
    print("• 📁 文件操作：保存、读取、创建项目结构")
    print("• ⚡ 命令执行：安全执行npm和shell命令")
    print("• 📊 项目监控：状态获取、结构分析、文件监控")
    print("• 📈 状态反馈：实时进度跟踪和状态管理")

if __name__ == "__main__":
    main()