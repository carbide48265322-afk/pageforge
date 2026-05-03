#!/usr/bin/env python3
"""
WebContainer API 使用示例
展示如何使用 WebContainer 后端 API
"""

import requests
import json
import time
from typing import Dict, Any

class WebContainerClient:
    """WebContainer API 客户端"""

    def __init__(self, base_url: str = "http://localhost:9565"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"

    def create_session(self) -> str:
        """创建新会话"""
        response = requests.post(f"{self.api_base}/sessions")
        response.raise_for_status()
        return response.json()["session_id"]

    def create_project(self, session_id: str, version: int) -> Dict[str, Any]:
        """创建 WebContainer 项目"""
        response = requests.post(
            f"{self.api_base}/webcontainer/projects",
            params={"session_id": session_id, "version": version}
        )
        response.raise_for_status()
        return response.json()

    def get_project_status(self, session_id: str, version: int) -> Dict[str, Any]:
        """获取项目状态"""
        response = requests.get(
            f"{self.api_base}/webcontainer/projects/{session_id}/{version}/status"
        )
        response.raise_for_status()
        return response.json()

    def install_dependencies(self, session_id: str, version: int) -> Dict[str, Any]:
        """安装依赖"""
        response = requests.post(
            f"{self.api_base}/webcontainer/projects/{session_id}/{version}/install"
        )
        response.raise_for_status()
        return response.json()

    def start_dev_server(self, session_id: str, version: int) -> Dict[str, Any]:
        """启动开发服务器"""
        response = requests.post(
            f"{self.api_base}/webcontainer/projects/{session_id}/{version}/start"
        )
        response.raise_for_status()
        return response.json()

    def get_project_files(self, session_id: str, version: int) -> Dict[str, Any]:
        """获取项目文件"""
        response = requests.get(
            f"{self.api_base}/webcontainer/projects/{session_id}/{version}/files"
        )
        response.raise_for_status()
        return response.json()

    def build_project(self, session_id: str, version: int) -> Dict[str, Any]:
        """构建项目"""
        response = requests.post(
            f"{self.api_base}/webcontainer/projects/{session_id}/{version}/build"
        )
        response.raise_for_status()
        return response.json()

    def cleanup_project(self, session_id: str, version: int) -> Dict[str, Any]:
        """清理项目"""
        response = requests.delete(
            f"{self.api_base}/webcontainer/projects/{session_id}/{version}"
        )
        response.raise_for_status()
        return response.json()


def main():
    """WebContainer API 使用示例"""

    print("🚀 WebContainer API 使用示例")
    print("=" * 50)

    client = WebContainerClient()

    try:
        # 1. 创建会话
        print("\n1. 创建会话...")
        session_id = client.create_session()
        print(f"✅ 会话创建成功: {session_id}")

        # 2. 创建项目
        print("\n2. 创建 WebContainer 项目...")
        version = 1
        project_result = client.create_project(session_id, version)
        print(f"✅ 项目创建成功:")
        print(f"   路径: {project_result['project_path']}")
        print(f"   文件: {', '.join(project_result['files'])}")

        # 3. 检查项目状态
        print("\n3. 检查项目状态...")
        status = client.get_project_status(session_id, version)
        print(f"✅ 项目状态: {status['status']}")
        print(f"   现有文件: {len(status['existing_files'])}")
        print(f"   缺失文件: {len(status['missing_files'])}")
        print(f"   依赖安装: {'✓' if status['has_node_modules'] else '✗'}")

        # 4. 安装依赖
        print("\n4. 安装依赖...")
        print("   这可能需要几分钟时间，请耐心等待...")
        install_result = client.install_dependencies(session_id, version)
        if install_result['status'] == 'success':
            print("✅ 依赖安装成功")
            print(f"   输出: {install_result.get('stdout', '无')[:100]}...")
        else:
            print(f"❌ 依赖安装失败: {install_result.get('error', '未知错误')}")
            return

        # 5. 再次检查状态
        print("\n5. 重新检查项目状态...")
        status = client.get_project_status(session_id, version)
        print(f"   依赖安装: {'✓' if status['has_node_modules'] else '✗'}")
        print(f"   依赖包: {list(status['dependencies'].keys())}")

        # 6. 启动开发服务器
        print("\n6. 启动开发服务器...")
        server_result = client.start_dev_server(session_id, version)
        if server_result['status'] == 'success':
            print("✅ 开发服务器启动成功")
            print(f"   URL: {server_result['url']}")
            print(f"   端口: {server_result['port']}")
            print(f"   PID: {server_result['pid']}")
        else:
            print(f"❌ 服务器启动失败: {server_result.get('error', '未知错误')}")

        # 7. 查看项目文件
        print("\n7. 查看项目文件...")
        files = client.get_project_files(session_id, version)
        print(f"   项目路径: {files['project_path']}")
        print(f"   文件数量: {len(files['files'])}")

        for file_path, file_info in files['files'].items():
            print(f"   📄 {file_path} ({file_info['size']} bytes)")

        # 8. 构建项目
        print("\n8. 构建项目...")
        build_result = client.build_project(session_id, version)
        if build_result['status'] == 'success':
            print("✅ 项目构建成功")
            if 'build_files' in build_result:
                print(f"   构建文件: {', '.join(build_result['build_files'])}")
        else:
            print(f"❌ 项目构建失败: {build_result.get('error', '未知错误')}")

        print("\n🎉 WebContainer 项目设置完成！")
        print(f"   会话 ID: {session_id}")
        print(f"   版本: {version}")
        if server_result.get('status') == 'success':
            print(f"   开发服务器: {server_result['url']}")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ API 请求失败: {e}")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
    finally:
        # 9. 清理项目（可选）
        print("\n9. 清理项目...")
        try:
            cleanup_result = client.cleanup_project(session_id, version)
            if cleanup_result['status'] == 'success':
                print("✅ 项目清理完成")
            else:
                print(f"⚠️  清理失败: {cleanup_result.get('error', '未知错误')}")
        except:
            print("⚠️  清理失败")


def demo_html_generation():
    """演示 HTML 生成和项目创建"""

    print("\n🎨 HTML 生成和项目创建演示")
    print("=" * 50)

    # 模拟 AI 生成的 HTML
    sample_html = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI 生成的页面</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                text-align: center;
            }
            .counter {
                background: rgba(255,255,255,0.1);
                border-radius: 15px;
                padding: 30px;
                margin: 30px 0;
            }
            .count {
                font-size: 4rem;
                font-weight: bold;
                margin: 20px 0;
            }
            button {
                background: rgba(255,255,255,0.2);
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                color: white;
                font-size: 1.1rem;
                cursor: pointer;
                margin: 0 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎉 AI 生成的计数器应用</h1>
            <div class="counter">
                <div class="count" id="counter">0</div>
                <button onclick="decrement()">-</button>
                <button onclick="reset()">重置</button>
                <button onclick="increment()">+</button>
            </div>
        </div>

        <script>
            let count = 0;

            function increment() {
                count++;
                updateDisplay();
            }

            function decrement() {
                count--;
                updateDisplay();
            }

            function reset() {
                count = 0;
                updateDisplay();
            }

            function updateDisplay() {
                document.getElementById('counter').textContent = count;
            }
        </script>
    </body>
    </html>
    """

    print("📄 示例 HTML 内容:")
    print("-" * 30)
    print(sample_html[:200] + "..." if len(sample_html) > 200 else sample_html)

    print("\n🔧 项目结构转换:")
    print("   index.html  ← 完整的 HTML 结构")
    print("   src/style.css  ← 提取的 CSS 样式")
    print("   src/main.js  ← 提取的 JavaScript")
    print("   package.json  ← 项目配置文件")

    print("\n🚀 启动流程:")
    print("   1. 创建项目文件结构")
    print("   2. 安装 npm 依赖 (react, vite)")
    print("   3. 启动开发服务器")
    print("   4. 在浏览器中预览和交互")


if __name__ == "__main__":
    # 运行演示
    demo_html_generation()

    print("\n" + "=" * 50)
    print("是否要运行完整的 API 示例？(y/N)")

    choice = input().strip().lower()
    if choice == 'y':
        main()
    else:
        print("\n💡 提示: 要运行完整示例，请确保:")
        print("   1. 后端服务正在运行 (uvicorn app.main:app --reload)")
        print("   2. 已安装所有依赖 (uv sync)")
        print("   3. 有可用的网络连接")
        print("\n然后再次运行此脚本并选择 'y'。")