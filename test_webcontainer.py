#!/usr/bin/env python3
"""
WebContainer 功能测试脚本
测试完整的项目创建和运行流程
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

# 配置
API_BASE = "http://localhost:9565/api"

class WebContainerTester:
    def __init__(self):
        self.session = None
        self.session_id = None
        self.version = 1

    async def test_all_templates(self):
        """测试所有可用模板"""
        print("🚀 开始测试所有 React 模板...")

        # 获取可用模板
        templates = await self.get_templates()
        print(f"✅ 获取到 {len(templates)} 个模板")

        for template_name, template_info in templates.items():
            print(f"\n📋 测试模板: {template_info['name']} ({template_name})")
            print(f"   描述: {template_info['description']}")
            print(f"   特性: {', '.join(template_info['features'])}")

            try:
                await self.test_single_template(template_name)
                print(f"✅ 模板 {template_name} 测试成功")
            except Exception as e:
                print(f"❌ 模板 {template_name} 测试失败: {e}")

    async def test_single_template(self, template_name: str):
        """测试单个模板的完整流程"""
        print(f"   1. 创建会话...")
        await self.create_session()

        print(f"   2. 从模板创建项目...")
        await self.create_from_template(template_name)

        print(f"   3. 检查项目状态...")
        await self.check_project_status()

        print(f"   4. 安装依赖...")
        await self.install_dependencies()

        print(f"   5. 获取项目文件...")
        await self.get_project_files()

        print(f"   6. 清理项目...")
        await self.cleanup_project()

    async def create_session(self):
        """创建新会话"""
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{API_BASE}/sessions") as resp:
                if resp.status != 200:
                    raise Exception(f"创建会话失败: {resp.status}")
                result = await resp.json()
                self.session_id = result["session_id"]
                print(f"   ✅ 会话创建成功: {self.session_id}")

    async def create_from_template(self, template_name: str):
        """从模板创建项目"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "session_id": self.session_id,
                "version": self.version,
                "template_name": template_name
            }

            async with session.post(
                f"{API_BASE}/webcontainer/projects/template",
                json=payload
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"从模板创建项目失败: {resp.status}")
                result = await resp.json()
                print(f"   ✅ 项目创建成功: {len(result['files'])} 个文件")

    async def check_project_status(self):
        """检查项目状态"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE}/webcontainer/projects/{self.session_id}/{self.version}/status"
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"获取项目状态失败: {resp.status}")
                result = await resp.json()
                print(f"   ✅ 项目状态: {result['status']}")
                print(f"   📁 现有文件: {len(result['existing_files'])}")

    async def install_dependencies(self):
        """安装依赖"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE}/webcontainer/projects/{self.session_id}/{self.version}/install"
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"安装依赖失败: {resp.status}")
                result = await resp.json()
                print(f"   ✅ 依赖安装: {result['status']}")

    async def get_project_files(self):
        """获取项目文件"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE}/webcontainer/projects/{self.session_id}/{self.version}/files"
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"获取文件失败: {resp.status}")
                result = await resp.json()
                print(f"   ✅ 项目文件: {len(result['files'])} 个文件")

                # 显示关键文件
                key_files = ['package.json', 'src/App.jsx', 'index.html', 'vite.config.js']
                for file in key_files:
                    if file in result['files']:
                        content = result['files'][file]['content'][:100] + '...'
                        print(f"   📄 {file}: {content}")

    async def cleanup_project(self):
        """清理项目"""
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"{API_BASE}/webcontainer/projects/{self.session_id}/{self.version}"
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"清理项目失败: {resp.status}")
                result = await resp.json()
                print(f"   ✅ 项目清理: {result['status']}")

    async def get_templates(self):
        """获取可用模板列表"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_BASE}/webcontainer/templates") as resp:
                if resp.status != 200:
                    raise Exception(f"获取模板失败: {resp.status}")
                return await resp.json()

    async def test_basic_apis(self):
        """测试基本 API 功能"""
        print("🔧 测试基本 API...")

        # 测试获取模板
        templates = await self.get_templates()
        print(f"✅ 模板 API 正常: {len(templates)} 个模板")

        # 创建会话
        await self.create_session()

        # 测试普通项目创建
        print("📦 测试普通项目创建...")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE}/webcontainer/projects?session_id={self.session_id}&version={self.version}"
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"创建项目失败: {resp.status}")
                result = await resp.json()
                print(f"✅ 普通项目创建成功: {len(result['files'])} 个文件")

        # 清理
        await self.cleanup_project()

async def main():
    """主测试函数"""
    print("🎯 WebContainer 功能测试开始")
    print("=" * 50)

    tester = WebContainerTester()

    try:
        # 测试基本 API
        await tester.test_basic_apis()

        # 测试所有模板
        await tester.test_all_templates()

        print("\n" + "=" * 50)
        print("🎉 所有测试完成！")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        raise

if __name__ == "__main__":
    # 检查后端服务是否可用
    import requests
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务正常")
        else:
            print(f"❌ 后端服务异常: {response.status_code}")
            exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到后端服务: {e}")
        print("请确保后端服务已启动 (python -m uvicorn app.main:app --reload)")
        exit(1)

    # 运行测试
    asyncio.run(main())