#!/usr/bin/env python3
"""
React 项目生成示例
展示 WebContainer 如何创建完整的 React 项目
"""

from app.services.webcontainer_service import WebContainerService

def create_todo_app_example():
    """创建待办事项应用的 React 项目示例"""

    # 模拟 AI 生成的 HTML
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>待办事项应用</title>
        <style>
            .app { max-width: 600px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif; }
            .header { text-align: center; color: #333; margin-bottom: 30px; }
            .input-group { display: flex; margin-bottom: 20px; }
            .input-group input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px 0 0 4px; }
            .input-group button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 0 4px 4px 0; cursor: pointer; }
            .todo-list { list-style: none; padding: 0; }
            .todo-item { display: flex; align-items: center; padding: 10px; border-bottom: 1px solid #eee; }
            .todo-item.completed { background-color: #f8f9fa; }
            .todo-text { flex: 1; margin: 0 10px; }
            .todo-text.completed { text-decoration: line-through; color: #6c757d; }
            .btn { padding: 5px 10px; border: none; border-radius: 3px; cursor: pointer; }
            .btn-toggle { background: #28a745; color: white; }
            .btn-delete { background: #dc3545; color: white; }
        </style>
    </head>
    <body>
        <div class="app">
            <h1 class="header">📝 待办事项管理</h1>
            <div class="input-group">
                <input type="text" id="todoInput" placeholder="添加新任务...">
                <button onclick="addTodo()">添加</button>
            </div>
            <ul id="todoList" class="todo-list"></ul>
        </div>

        <script>
            let todos = JSON.parse(localStorage.getItem('todos') || '[]');
            const todoInput = document.getElementById('todoInput');
            const todoList = document.getElementById('todoList');

            function addTodo() {
                if (todoInput.value.trim()) {
                    const todo = {
                        id: Date.now(),
                        text: todoInput.value.trim(),
                        completed: false,
                        createdAt: new Date().toISOString()
                    };
                    todos.push(todo);
                    saveTodos();
                    renderTodos();
                    todoInput.value = '';
                }
            }

            function toggleTodo(id) {
                todos = todos.map(todo =>
                    todo.id === id ? { ...todo, completed: !todo.completed } : todo
                );
                saveTodos();
                renderTodos();
            }

            function deleteTodo(id) {
                todos = todos.filter(todo => todo.id !== id);
                saveTodos();
                renderTodos();
            }

            function saveTodos() {
                localStorage.setItem('todos', JSON.stringify(todos));
            }

            function renderTodos() {
                todoList.innerHTML = todos.map(todo => `
                    <li class="todo-item ${todo.completed ? 'completed' : ''}" data-id="${todo.id}">
                        <button class="btn btn-toggle" onclick="toggleTodo(${todo.id})">
                            ${todo.completed ? '✓' : '○'}
                        </button>
                        <span class="todo-text ${todo.completed ? 'completed' : ''}">${todo.text}</span>
                        <button class="btn btn-delete" onclick="deleteTodo(${todo.id})">删除</button>
                    </li>
                `).join('');
            }

            // 回车添加
            todoInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    addTodo();
                }
            });

            // 初始化渲染
            renderTodos();
        </script>
    </body>
    </html>
    """

    # 创建 WebContainer 服务
    service = WebContainerService()

    # 解析 HTML 为 React 项目
    files = service._parse_html_to_project(html_content)

    print("🚀 React 项目文件结构生成完成！")
    print("=" * 50)

    for filename, content in files.items():
        print(f"\n📄 {filename}:")
        print("-" * 30)
        if filename.endswith('.json'):
            print(content[:500] + "..." if len(content) > 500 else content)
        else:
            print(content[:800] + "..." if len(content) > 800 else content)

    return files

def create_counter_app_example():
    """创建计数器应用的 React 项目示例"""

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f0f2f5; }
            .counter { text-align: center; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .count { font-size: 4rem; font-weight: bold; color: #007bff; margin: 20px 0; }
            .buttons { display: flex; gap: 10px; justify-content: center; }
            button { padding: 10px 20px; font-size: 1.1rem; border: none; border-radius: 5px; cursor: pointer; }
            .btn-decrease { background: #dc3545; color: white; }
            .btn-reset { background: #6c757d; color: white; }
            .btn-increase { background: #28a745; color: white; }
        </style>
    </head>
    <body>
        <div class="counter">
            <h1>计数器</h1>
            <div id="count" class="count">0</div>
            <div class="buttons">
                <button class="btn-decrease" onclick="changeCount(-1)">-</button>
                <button class="btn-reset" onclick="resetCount()">重置</button>
                <button class="btn-increase" onclick="changeCount(1)">+</button>
            </div>
        </div>

        <script>
            let count = parseInt(localStorage.getItem('counter') || '0');
            const countDisplay = document.getElementById('count');

            function updateDisplay() {
                countDisplay.textContent = count;
                localStorage.setItem('counter', count.toString());

                // 添加动画效果
                countDisplay.style.transform = 'scale(1.2)';
                setTimeout(() => {
                    countDisplay.style.transform = 'scale(1)';
                }, 150);
            }

            function changeCount(delta) {
                count += delta;
                updateDisplay();
            }

            function resetCount() {
                count = 0;
                updateDisplay();
            }

            // 初始化
            updateDisplay();
        </script>
    </body>
    </html>
    """

    service = WebContainerService()
    files = service._parse_html_to_project(html_content)

    print("\n🎯 计数器 React 项目:")
    print("=" * 50)

    # 显示 App.jsx 内容
    if 'src/App.jsx' in files:
        print("\n📄 src/App.jsx (React 组件):")
        print("-" * 40)
        print(files['src/App.jsx'])

    return files

def main():
    """主函数 - 演示完整的 React 项目生成"""

    print("🎨 WebContainer React 项目生成演示")
    print("=" * 60)

    # 1. 创建待办事项应用
    todo_files = create_todo_app_example()

    # 2. 创建计数器应用
    counter_files = create_counter_app_example()

    print("\n📊 项目统计:")
    print("=" * 30)
    print(f"待办事项项目文件数: {len(todo_files)}")
    print(f"计数器项目文件数: {len(counter_files)}")

    print("\n🏗️  生成的文件类型:")
    print("   📦 package.json - 项目配置和依赖")
    print("   ⚙️  vite.config.js - 构建配置")
    print("   📄 index.html - 入口 HTML")
    print("   ⚛️  src/main.jsx - React 入口")
    print("   🎨 src/index.css - 全局样式")
    print("   🧩 src/App.jsx - 主组件")
    print("   🖼️ public/vite.svg - 应用图标")

    print("\n🚀 项目特点:")
    print("   ✅ 完整的 React 18 + Vite 项目结构")
    print("   ✅ 自动转换 HTML 为 JSX")
    print("   ✅ 自动转换 JavaScript 为 React Hooks")
    print("   ✅ 支持 localStorage 状态持久化")
    print("   ✅ 响应式设计和现代 UI")
    print("   ✅ 完整的开发工具链")

    print("\n💡 使用方式:")
    print("   1. 创建项目: POST /api/webcontainer/projects")
    print("   2. 安装依赖: POST /api/webcontainer/projects/{id}/{version}/install")
    print("   3. 启动开发: POST /api/webcontainer/projects/{id}/{version}/start")
    print("   4. 访问应用: http://localhost:6000")

if __name__ == "__main__":
    main()