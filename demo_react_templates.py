#!/usr/bin/env python3
"""
React 模板功能演示脚本
展示如何使用新的 React 模板功能
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

API_BASE = "http://localhost:9565/api"

async def demo_react_templates():
    """演示 React 模板功能"""
    print("🎨 React 模板功能演示")
    print("=" * 50)

    # 1. 获取可用模板
    print("\n📋 获取可用模板列表...")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}/webcontainer/templates") as resp:
            templates = await resp.json()

    print(f"✅ 发现 {len(templates)} 个模板:")
    for template_id, info in templates.items():
        print(f"  • {info['name']} ({template_id})")
        print(f"    描述: {info['description']}")
        print(f"    特性: {', '.join(info['features'])}")
        print()

    # 2. 演示创建不同模板
    demo_templates = ['counter', 'todo', 'chat', 'charts']

    for template_name in demo_templates:
        if template_name in templates:
            print(f"🔧 演示创建 {templates[template_name]['name']} 项目...")
            await demo_create_template(template_name, templates[template_name]['name'])
            print()

async def demo_create_template(template_name: str, display_name: str):
    """演示创建指定模板"""
    # 创建会话
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_BASE}/sessions") as resp:
            session_data = await resp.json()
            session_id = session_data["session_id"]

    print(f"  1. 创建会话: {session_id}")

    # 从模板创建项目
    version = 1
    async with aiohttp.ClientSession() as session:
        payload = {
            "session_id": session_id,
            "version": version,
            "template_name": template_name
        }

        async with session.post(
            f"{API_BASE}/webcontainer/projects/template",
            json=payload
        ) as resp:
            project_data = await resp.json()

    print(f"  2. 项目创建成功!")
    print(f"     • 项目路径: {project_data['project_path']}")
    print(f"     • 文件数量: {len(project_data['files'])}")
    print(f"     • 模板类型: {project_data['template']}")

    # 显示项目文件结构
    print(f"  3. 项目文件结构:")
    for file_path in sorted(project_data['files']):
        print(f"     📄 {file_path}")

    # 获取项目详情
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{API_BASE}/webcontainer/projects/{session_id}/{version}/files"
        ) as resp:
            files_data = await resp.json()

    # 显示关键文件内容
    key_files = ['package.json', 'src/App.jsx', 'vite.config.js']
    for file_name in key_files:
        if file_name in files_data['files']:
            content = files_data['files'][file_name]['content']
            print(f"\n  4. {file_name} 内容预览:")
            print(f"     {'-' * 40}")
            lines = content.split('\n')[:10]  # 显示前10行
            for line in lines:
                print(f"     {line}")
            if len(lines) < len(content.split('\n')):
                print("     ...")

    # 清理项目
    async with aiohttp.ClientSession() as session:
        async with session.delete(
            f"{API_BASE}/webcontainer/projects/{session_id}/{version}"
        ) as resp:
            cleanup_result = await resp.json()

    print(f"  5. 项目清理: {cleanup_result['status']}")

async def demo_template_comparison():
    """演示不同模板的对比"""
    print("\n📊 模板功能对比演示")
    print("=" * 50)

    templates = [
        ('counter', '计数器应用'),
        ('todo', '待办事项管理'),
        ('calculator', '计算器应用'),
        ('weather', '天气查询'),
        ('chat', '聊天应用'),
        ('blog', '博客系统'),
        ('charts', '数据可视化')
    ]

    print("\n功能特性对比:")
    print(f"{'模板名称':<15} {'React Hooks':<12} {'本地存储':<10} {'响应式设计':<12} {'特色功能':<15}")
    print("-" * 70)

    for template_id, template_name in templates:
        features = await get_template_features(template_id)
        hooks = '✓' if 'hooks' in features else '○'
        storage = '✓' if 'localStorage' in features else '○'
        responsive = '✓' if 'responsive' in features else '○'
        special = get_special_feature(template_id)

        print(f"{template_name:<15} {hooks:<12} {storage:<10} {responsive:<12} {special:<15}")

async def get_template_features(template_id: str) -> list:
    """获取模板特性"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}/webcontainer/templates") as resp:
            templates = await resp.json()
            return templates.get(template_id, {}).get('features', [])

def get_special_feature(template_id: str) -> str:
    """获取模板特殊功能"""
    features = {
        'counter': '状态管理',
        'todo': '任务过滤',
        'calculator': '数学运算',
        'weather': '数据查询',
        'chat': '实时消息',
        'blog': '文章管理',
        'charts': '数据可视化'
    }
    return features.get(template_id, '基础功能')

async def main():
    """主演示函数"""
    print("🚀 React 模板系统演示")
    print("演示完整的 React 项目创建流程")

    try:
        # 演示模板功能
        await demo_react_templates()

        # 演示模板对比
        await demo_template_comparison()

        print("\n" + "=" * 50)
        print("🎉 演示完成！")
        print("\n使用指南:")
        print("1. 选择适合的模板")
        print("2. 调用 create_project_from_template API")
        print("3. 安装依赖并启动开发服务器")
        print("4. 在浏览器中查看运行效果")

    except Exception as e:
        print(f"❌ 演示失败: {e}")
        raise

if __name__ == "__main__":
    # 检查服务可用性
    import requests
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ 服务不可用: {response.status_code}")
            exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接服务: {e}")
        print("请先启动后端服务: python -m uvicorn app.main:app --reload")
        exit(1)

    # 运行演示
    asyncio.run(main())