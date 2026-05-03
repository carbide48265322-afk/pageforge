import os
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import HTTPException

from app.services.session_service import SessionService
from app.services.version_service import VersionService


class WebContainerService:
    """WebContainer 服务 - 管理浏览器内项目运行环境"""

    def __init__(self):
        self.session_service = SessionService()
        self.version_service = VersionService()
        self.temp_dir = Path(tempfile.gettempdir()) / "pageforge_webcontainer"
        self.temp_dir.mkdir(exist_ok=True)

    def _get_project_dir(self, session_id: str, version: int) -> Path:
        """获取项目目录路径"""
        return self.temp_dir / session_id / f"v{version}"

    def _create_react_project_from_config(self, config: Dict[str, Any]) -> Dict[str, str]:
        """根据配置创建完整的 React 项目"""
        files = {}

        # 1. package.json
        package_json = {
            "name": config["name"],
            "version": "0.1.0",
            "private": true,
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "lint": "eslint . --ext js,jsx --report-unused-disable-directives --max-warnings 0",
                "preview": "vite preview"
            },
            "dependencies": {},
            "devDependencies": {}
        }

        # 添加依赖
        for dep in config.get("dependencies", []):
            package_json["dependencies"][dep] = self._get_dependency_version(dep)

        for dev_dep in config.get("dev_dependencies", []):
            package_json["devDependencies"][dev_dep] = self._get_dependency_version(dev_dep)

        files['package.json'] = json.dumps(package_json, indent=2, ensure_ascii=False)

        # 2. vite.config.js
        files['vite.config.js'] = '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 6000
  }
})'''

        # 3. index.html
        files['index.html'] = '''<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>''' + config["name"] + '''</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>'''

        # 4. src/main.jsx
        files['src/main.jsx'] = '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from \'./App.jsx\'
import \'./index.css\'

ReactDOM.createRoot(document.getElementById(\'root\')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)'''

        # 5. src/index.css
        files['src/index.css'] = '''* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', \'Roboto\', \'Oxygen\',
    \'Ubuntu\', \'Cantarell\', \'Fira Sans\', \'Droid Sans\', \'Helvetica Neue\',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, \'Courier New\',
    monospace;
}'''

        # 6. src/App.jsx - 根据模板生成
        files['src/App.jsx'] = self._generate_app_component(config)

        # 7. 额外的组件文件
        for component_name, component_type in config.get("components", {}).items():
            if component_name != "App":
                files[f'src/components/{component_name}.jsx'] = self._generate_component(component_name, component_type, config)

        # 8. public/vite.svg
        files['public/vite.svg'] = '''<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 256 257"><defs><linearGradient id="a" x1="-.828%" x2="57.632%" y1="7.652%" y2="78.411%"><stop offset="0%"></stop><stop offset="100%"></stop></linearGradient><linearGradient id="b" x1="43.376%" x2="50.316%" y1="2.242%" y2="89.03%"><stop offset="0%"></stop><stop offset="100%"></stop></linearGradient></defs><path fill="url(#a)" d="M255.153 37.938L134.897 252.976c-2.483 4.44-8.862 4.466-11.382.048L.325 37.958c-2.746-4.814 1.371-10.646 6.827-9.67l120.385 21.517a6.537 6.537 0 0 0 2.322-.004l114.786-22.053c5.438-.494 9.574 4.778 6.877 9.62Z"></path><path fill="url(#b)" d="M185.432.063L96.44 17.501a3.268 3.268 0 0 0-2.634 3.014l-5.474 92.456a3.268 3.268 0 0 0 1.918 3.218l84.221 4.147c4.467.221 8.165-2.804 9.481-7.412l8.979-38.11a13.31 13.31 0 0 0-1.048-7.09l-10.112-19.029a13.31 13.31 0 0 0-7.683-6.785l-13.948-4.994Z"></path></svg>'''

        return files

    def _get_dependency_version(self, package_name: str) -> str:
        """获取依赖包版本"""
        versions = {
            "react": "^19.0.0",
            "react-dom": "^19.0.0",
            "lucide-react": "^0.344.0",
            "@vitejs/plugin-react": "^4.2.1",
            "@types/react": "^19.0.0",
            "@types/react-dom": "^19.0.0",
            "vite": "^5.1.0",
            "eslint": "^8.56.0",
            "eslint-plugin-react": "^7.34.0",
            "eslint-plugin-react-hooks": "^4.6.0",
            "eslint-plugin-react-refresh": "^0.4.5"
        }
        return versions.get(package_name, "^1.0.0")

    def _generate_app_component(self, config: Dict[str, Any]) -> str:
        """生成主 App 组件"""
        template_name = config.get("template", "counter")

        templates = {
            "counter": self._generate_counter_app,
            "todo": self._generate_todo_app,
            "calculator": self._generate_calculator_app,
            "weather": self._generate_weather_app,
            "chat": self._generate_chat_app,
            "blog": self._generate_blog_app,
            "charts": self._generate_charts_app
        }

        if template_name in templates:
            return templates[template_name](config)
        else:
            return self._generate_counter_app(config)  # 默认模板

    def _generate_counter_app(self, config: Dict[str, Any]) -> str:
        """生成计数器应用组件"""
        return '''import React, { useState, useEffect } from 'react'

function App() {
  const [count, setCount] = useState(() => {
    const saved = localStorage.getItem('counter');
    return saved ? parseInt(saved) : 0;
  })

  useEffect(() => {
    localStorage.setItem('counter', count.toString());
  }, [count])

  const increment = () => setCount(count + 1)
  const decrement = () => setCount(count - 1)
  const reset = () => setCount(0)

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-8">
          🔢 计数器
        </h1>

        <div className="text-center mb-8">
          <div
            className="text-6xl font-bold text-blue-600 mb-4 transition-transform duration-200 hover:scale-110"
            style={{ transform: count !== 0 ? 'scale(1.1)' : 'scale(1)' }}
          >
            {count}
          </div>
          <p className="text-gray-600">当前计数</p>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <button
            onClick={decrement}
            className="bg-red-500 hover:bg-red-600 text-white font-bold py-3 px-6 rounded-lg transition-colors duration-200 transform hover:scale-105"
          >
            -1
          </button>

          <button
            onClick={reset}
            className="bg-gray-500 hover:bg-gray-600 text-white font-bold py-3 px-6 rounded-lg transition-colors duration-200 transform hover:scale-105"
          >
            重置
          </button>

          <button
            onClick={increment}
            className="bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-6 rounded-lg transition-colors duration-200 transform hover:scale-105"
          >
            +1
          </button>
        </div>

        <div className="mt-8 text-center text-sm text-gray-500">
          <p>计数已保存到本地存储</p>
          <p className="mt-2">刷新页面后数据依然存在 💾</p>
        </div>
      </div>
    </div>
  )
}

export default App'''

    def _generate_todo_app(self, config: Dict[str, Any]) -> str:
        """生成待办事项应用组件"""
        return '''import React, { useState, useEffect } from 'react'
import { Plus, Trash2, Check, Circle } from 'lucide-react'

function App() {
  const [todos, setTodos] = useState(() => {
    const saved = localStorage.getItem('todos');
    return saved ? JSON.parse(saved) : [];
  })
  const [newTodo, setNewTodo] = useState('')
  const [filter, setFilter] = useState('all') // all, active, completed

  useEffect(() => {
    localStorage.setItem('todos', JSON.stringify(todos));
  }, [todos])

  const addTodo = () => {
    if (newTodo.trim()) {
      const todo = {
        id: Date.now(),
        text: newTodo.trim(),
        completed: false,
        createdAt: new Date().toISOString()
      }
      setTodos([...todos, todo])
      setNewTodo('')
    }
  }

  const toggleTodo = (id) => {
    setTodos(todos.map(todo =>
      todo.id === id ? { ...todo, completed: !todo.completed } : todo
    ))
  }

  const deleteTodo = (id) => {
    setTodos(todos.filter(todo => todo.id !== id))
  }

  const clearCompleted = () => {
    setTodos(todos.filter(todo => !todo.completed))
  }

  const filteredTodos = todos.filter(todo => {
    if (filter === 'active') return !todo.completed
    if (filter === 'completed') return todo.completed
    return true
  })

  const completedCount = todos.filter(todo => todo.completed).length
  const activeCount = todos.length - completedCount

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-500 to-purple-600 p-4">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <h1 className="text-4xl font-bold text-center text-gray-800 mb-8">
            📝 待办事项
          </h1>

          {/* 添加新任务 */}
          <div className="flex gap-2 mb-6">
            <input
              type="text"
              value={newTodo}
              onChange={(e) => setNewTodo(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addTodo()}
              placeholder="添加新任务..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              onClick={addTodo}
              className="bg-indigo-500 hover:bg-indigo-600 text-white px-6 py-3 rounded-lg transition-colors duration-200 flex items-center gap-2"
            >
              <Plus size={20} />
              添加
            </button>
          </div>

          {/* 过滤器 */}
          <div className="flex gap-2 mb-6">
            {['all', 'active', 'completed'].map(filterType => (
              <button
                key={filterType}
                onClick={() => setFilter(filterType)}
                className={`px-4 py-2 rounded-lg transition-colors duration-200 ${
                  filter === filterType
                    ? 'bg-indigo-500 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {filterType === 'all' ? '全部' : filterType === 'active' ? '未完成' : '已完成'}
              </button>
            ))}
          </div>

          {/* 任务列表 */}
          <div className="space-y-3 mb-6">
            {filteredTodos.map(todo => (
              <div
                key={todo.id}
                className={`flex items-center gap-3 p-4 rounded-lg border transition-colors duration-200 ${
                  todo.completed
                    ? 'bg-gray-50 border-gray-200'
                    : 'bg-white border-gray-300'
                }`}
              >
                <button
                  onClick={() => toggleTodo(todo.id)}
                  className={`flex-shrink-0 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors duration-200 ${
                    todo.completed
                      ? 'bg-green-500 border-green-500 text-white'
                      : 'border-gray-300 hover:border-green-500'
                  }`}
                >
                  {todo.completed && <Check size={14} />}
                </button>

                <span
                  className={`flex-1 ${
                    todo.completed
                      ? 'text-gray-500 line-through'
                      : 'text-gray-800'
                  }`}
                >
                  {todo.text}
                </span>

                <button
                  onClick={() => deleteTodo(todo.id)}
                  className="text-red-500 hover:text-red-700 transition-colors duration-200"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            ))}
          </div>

          {/* 统计信息 */}
          <div className="flex justify-between items-center text-sm text-gray-600 border-t pt-4">
            <span>总计: {todos.length} | 未完成: {activeCount} | 已完成: {completedCount}</span>
            {completedCount > 0 && (
              <button
                onClick={clearCompleted}
                className="text-red-500 hover:text-red-700 transition-colors duration-200"
              >
                清除已完成
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App'''

    def _generate_calculator_app(self, config: Dict[str, Any]) -> str:
        """生成计算器应用组件"""
        return '''import React, { useState } from 'react'

function App() {
  const [display, setDisplay] = useState('0')
  const [previousValue, setPreviousValue] = useState(null)
  const [operation, setOperation] = useState(null)
  const [waitingForOperand, setWaitingForOperand] = useState(false)

  const inputNumber = (num) => {
    if (waitingForOperand) {
      setDisplay(String(num))
      setWaitingForOperand(false)
    } else {
      setDisplay(display === '0' ? String(num) : display + num)
    }
  }

  const inputOperation = (nextOperation) => {
    const inputValue = parseFloat(display)

    if (previousValue === null) {
      setPreviousValue(inputValue)
    } else if (operation) {
      const currentValue = previousValue || 0
      const newValue = calculate(currentValue, inputValue, operation)

      setDisplay(String(newValue))
      setPreviousValue(newValue)
    }

    setWaitingForOperand(true)
    setOperation(nextOperation)
  }

  const calculate = (firstValue, secondValue, operation) => {
    switch (operation) {
      case '+':
        return firstValue + secondValue
      case '-':
        return firstValue - secondValue
      case '×':
        return firstValue * secondValue
      case '÷':
        return firstValue / secondValue
      case '=':
        return secondValue
      default:
        return secondValue
    }
  }

  const performCalculation = () => {
    const inputValue = parseFloat(display)

    if (previousValue !== null && operation) {
      const newValue = calculate(previousValue, inputValue, operation)
      setDisplay(String(newValue))
      setPreviousValue(null)
      setOperation(null)
      setWaitingForOperand(true)
    }
  }

  const clearAll = () => {
    setDisplay('0')
    setPreviousValue(null)
    setOperation(null)
    setWaitingForOperand(false)
  }

  const clearEntry = () => {
    setDisplay('0')
    setWaitingForOperand(false)
  }

  const Button = ({ onClick, className = '', children }) => (
    <button
      onClick={onClick}
      className={`bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-4 px-6 rounded-lg transition-colors duration-200 transform hover:scale-105 ${className}`}
    >
      {children}
    </button>
  )

  const OperatorButton = ({ onClick, children }) => (
    <button
      onClick={onClick}
      className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-4 px-6 rounded-lg transition-colors duration-200 transform hover:scale-105"
    >
      {children}
    </button>
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-6">
          🧮 计算器
        </h1>

        {/* 显示屏 */}
        <div className="bg-gray-900 text-white p-6 rounded-lg mb-6">
          <div className="text-right">
            <div className="text-2xl font-mono break-all">
              {display}
            </div>
            {operation && (
              <div className="text-sm text-gray-400 mt-2">
                {previousValue} {operation}
              </div>
            )}
          </div>
        </div>

        {/* 按钮网格 */}
        <div className="grid grid-cols-4 gap-3">
          <Button onClick={clearAll} className="col-span-2 bg-red-500 hover:bg-red-600 text-white">
            AC
          </Button>
          <Button onClick={clearEntry} className="bg-orange-500 hover:bg-orange-600 text-white">
            CE
          </Button>
          <OperatorButton onClick={() => inputOperation('÷')}>÷</OperatorButton>

          <Button onClick={() => inputNumber(7)}>7</Button>
          <Button onClick={() => inputNumber(8)}>8</Button>
          <Button onClick={() => inputNumber(9)}>9</Button>
          <OperatorButton onClick={() => inputOperation('×')}>×</OperatorButton>

          <Button onClick={() => inputNumber(4)}>4</Button>
          <Button onClick={() => inputNumber(5)}>5</Button>
          <Button onClick={() => inputNumber(6)}>6</Button>
          <OperatorButton onClick={() => inputOperation('-')}>-</OperatorButton>

          <Button onClick={() => inputNumber(1)}>1</Button>
          <Button onClick={() => inputNumber(2)}>2</Button>
          <Button onClick={() => inputNumber(3)}>3</Button>
          <OperatorButton onClick={() => inputOperation('+')}>+</OperatorButton>

          <Button onClick={() => inputNumber(0)} className="col-span-2">0</Button>
          <Button onClick={() => inputNumber('.')}>.</Button>
          <OperatorButton onClick={performCalculation}>=</OperatorButton>
        </div>

        <div className="mt-6 text-center text-sm text-gray-500">
          <p>支持基本四则运算</p>
          <p className="mt-1">点击按钮或使用键盘输入</p>
        </div>
      </div>
    </div>
  )
}

export default App'''

    def _generate_weather_app(self, config: Dict[str, Any]) -> str:
        """生成天气应用组件（模拟数据）"""
        return '''import React, { useState, useEffect } from 'react'
import { Search, MapPin, Thermometer, Droplets, Wind, Eye } from 'lucide-react'

function App() {
  const [city, setCity] = useState('北京')
  const [weather, setWeather] = useState({
    temperature: 22,
    condition: '晴朗',
    humidity: 65,
    windSpeed: 12,
    visibility: 10,
    location: '北京市',
    icon: '☀️'
  })
  const [searchCity, setSearchCity] = useState('')

  // 模拟天气数据
  const weatherData = {
    '北京': { temperature: 22, condition: '晴朗', humidity: 65, windSpeed: 12, visibility: 10, icon: '☀️' },
    '上海': { temperature: 26, condition: '多云', humidity: 78, windSpeed: 8, visibility: 8, icon: '☁️' },
    '广州': { temperature: 30, condition: '小雨', humidity: 85, windSpeed: 6, visibility: 5, icon: '🌧️' },
    '深圳': { temperature: 28, condition: '阴天', humidity: 80, windSpeed: 10, visibility: 7, icon: '☁️' },
    '杭州': { temperature: 24, condition: '晴朗', humidity: 70, windSpeed: 9, visibility: 12, icon: '☀️' }
  }

  const searchWeather = () => {
    if (searchCity.trim() && weatherData[searchCity]) {
      setCity(searchCity)
      setWeather({
        ...weatherData[searchCity],
        location: searchCity
      })
      setSearchCity('')
    }
  }

  const getCurrentTime = () => {
    return new Date().toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-400 to-purple-600 p-4">
      <div className="max-w-md mx-auto">
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8">
          <h1 className="text-3xl font-bold text-center text-white mb-8">
            🌤️ 天气查询
          </h1>

          {/* 搜索框 */}
          <div className="flex gap-2 mb-8">
            <input
              type="text"
              value={searchCity}
              onChange={(e) => setSearchCity(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && searchWeather()}
              placeholder="输入城市名称..."
              className="flex-1 px-4 py-3 bg-white/20 text-white placeholder-white/70 rounded-lg focus:outline-none focus:ring-2 focus:ring-white/50"
            />
            <button
              onClick={searchWeather}
              className="bg-white/20 hover:bg-white/30 text-white px-6 py-3 rounded-lg transition-colors duration-200 flex items-center gap-2"
            >
              <Search size={20} />
            </button>
          </div>

          {/* 天气信息 */}
          <div className="text-center text-white mb-8">
            <div className="flex items-center justify-center gap-2 mb-4">
              <MapPin size={20} />
              <span className="text-lg">{weather.location}</span>
            </div>

            <div className="text-6xl mb-4">{weather.icon}</div>

            <div className="text-5xl font-bold mb-2">{weather.temperature}°C</div>
            <div className="text-xl opacity-90">{weather.condition}</div>
            <div className="text-sm opacity-75 mt-2">
              更新时间: {getCurrentTime()}
            </div>
          </div>

          {/* 详细信息 */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-white/10 rounded-lg p-4 text-center">
              <Droplets className="mx-auto mb-2" size={24} />
              <div className="text-sm opacity-75">湿度</div>
              <div className="text-xl font-semibold">{weather.humidity}%</div>
            </div>

            <div className="bg-white/10 rounded-lg p-4 text-center">
              <Wind className="mx-auto mb-2" size={24} />
              <div className="text-sm opacity-75">风速</div>
              <div className="text-xl font-semibold">{weather.windSpeed} km/h</div>
            </div>

            <div className="bg-white/10 rounded-lg p-4 text-center">
              <Eye className="mx-auto mb-2" size={24} />
              <div className="text-sm opacity-75">能见度</div>
              <div className="text-xl font-semibold">{weather.visibility} km</div>
            </div>

            <div className="bg-white/10 rounded-lg p-4 text-center">
              <Thermometer className="mx-auto mb-2" size={24} />
              <div className="text-sm opacity-75">体感</div>
              <div className="text-xl font-semibold">{weather.temperature + 2}°C</div>
            </div>
          </div>

          {/* 支持的城市 */}
          <div className="text-center">
            <div className="text-white/75 text-sm mb-3">支持的城市:</div>
            <div className="flex flex-wrap gap-2 justify-center">
              {Object.keys(weatherData).map(cityName => (
                <button
                  key={cityName}
                  onClick={() => {
                    setCity(cityName)
                    setWeather({
                      ...weatherData[cityName],
                      location: cityName
                    })
                  }}
                  className={`px-3 py-1 rounded-full text-sm transition-colors duration-200 ${
                    city === cityName
                      ? 'bg-white text-blue-600'
                      : 'bg-white/20 text-white hover:bg-white/30'
                  }`}
                >
                  {cityName}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App'''

    def _generate_chat_app(self, config: Dict[str, Any]) -> str:
        """生成聊天应用组件"""
        return '''import React, { useState, useEffect, useRef } from 'react'
import { Send, User, Bot, Settings, LogOut } from 'lucide-react'

function App() {
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem('chatMessages');
    return saved ? JSON.parse(saved) : [
      { id: 1, text: '你好！我是你的AI助手，有什么可以帮助你的吗？', sender: 'bot', timestamp: new Date().toISOString() }
    ];
  })
  const [inputMessage, setInputMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [userName, setUserName] = useState(() => localStorage.getItem('userName') || '用户')
  const [isEditingName, setIsEditingName] = useState(false)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    localStorage.setItem('chatMessages', JSON.stringify(messages));
  }, [messages])

  useEffect(() => {
    localStorage.setItem('userName', userName);
  }, [userName])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(scrollToBottom, [messages])

  const sendMessage = () => {
    if (inputMessage.trim()) {
      const userMessage = {
        id: Date.now(),
        text: inputMessage.trim(),
        sender: 'user',
        timestamp: new Date().toISOString()
      }

      setMessages(prev => [...prev, userMessage])
      setInputMessage('')
      setIsTyping(true)

      // 模拟AI回复
      setTimeout(() => {
        const responses = [
          '这是一个很有趣的问题！让我想想...',
          '根据你的问题，我建议你可以考虑以下几个方面：',
          '很好的观察！这确实是一个值得深入探讨的话题。',
          '我理解你的困惑。让我们一起来分析一下。',
          '这个问题有几个不同的角度可以思考：'
        ]
        const randomResponse = responses[Math.floor(Math.random() * responses.length)]

        const botMessage = {
          id: Date.now() + 1,
          text: randomResponse,
          sender: 'bot',
          timestamp: new Date().toISOString()
        }

        setMessages(prev => [...prev, botMessage])
        setIsTyping(false)
      }, 1000 + Math.random() * 2000)
    }
  }

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const clearChat = () => {
    setMessages([{
      id: 1,
      text: '你好！我是你的AI助手，有什么可以帮助你的吗？',
      sender: 'bot',
      timestamp: new Date().toISOString()
    }])
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-500 to-pink-500 p-4">
      <div className="max-w-4xl mx-auto h-screen flex flex-col">
        {/* 头部 */}
        <div className="bg-white/10 backdrop-blur-lg rounded-t-2xl p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
              <Bot className="text-white" size={20} />
            </div>
            <div>
              <h1 className="text-white text-xl font-bold">AI 助手</h1>
              <p className="text-white/70 text-sm">在线</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {isEditingName ? (
              <input
                type="text"
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
                onBlur={() => setIsEditingName(false)}
                onKeyPress={(e) => e.key === 'Enter' && setIsEditingName(false)}
                className="bg-white/20 text-white px-3 py-1 rounded-lg focus:outline-none focus:ring-2 focus:ring-white/50"
                autoFocus
              />
            ) : (
              <div
                onClick={() => setIsEditingName(true)}
                className="flex items-center gap-2 text-white cursor-pointer hover:bg-white/10 px-3 py-1 rounded-lg transition-colors"
              >
                <User size={16} />
                <span>{userName}</span>
              </div>
            )}

            <button
              onClick={clearChat}
              className="text-white/70 hover:text-white transition-colors p-2 hover:bg-white/10 rounded-lg"
            >
              <Settings size={20} />
            </button>
          </div>
        </div>

        {/* 消息区域 */}
        <div className="flex-1 bg-white/5 backdrop-blur-sm p-6 overflow-y-auto">
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${
                    message.sender === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-white/20 text-white backdrop-blur-sm'
                  }`}
                >
                  <p className="text-sm">{message.text}</p>
                  <p className={`text-xs mt-1 ${
                    message.sender === 'user' ? 'text-blue-100' : 'text-white/70'
                  }`}>
                    {formatTime(message.timestamp)}
                  </p>
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-white/20 text-white backdrop-blur-sm px-4 py-3 rounded-2xl">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-white/60 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-white/60 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                    <div className="w-2 h-2 bg-white/60 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* 输入区域 */}
        <div className="bg-white/10 backdrop-blur-lg rounded-b-2xl p-4">
          <div className="flex gap-3">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="输入消息..."
              className="flex-1 bg-white/20 text-white placeholder-white/70 px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-white/50"
            />
            <button
              onClick={sendMessage}
              disabled={!inputMessage.trim()}
              className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-500 text-white px-6 py-3 rounded-lg transition-colors duration-200 flex items-center gap-2"
            >
              <Send size={20} />
            </button>
          </div>

          <div className="text-center text-white/60 text-xs mt-2">
            按 Enter 发送消息
          </div>
        </div>
      </div>
    </div>
  )
}

export default App'''

    def _generate_blog_app(self, config: Dict[str, Any]) -> str:
        """生成博客系统应用组件"""
        return '''import React, { useState, useEffect } from 'react'
import { Plus, Edit, Trash2, Calendar, User, Tag, Search, Filter } from 'lucide-react'

function App() {
  const [posts, setPosts] = useState(() => {
    const saved = localStorage.getItem('blogPosts');
    return saved ? JSON.parse(saved) : [
      {
        id: 1,
        title: '欢迎来到我的博客',
        content: '这是我的第一篇博客文章。在这里我将分享我的想法和经验。',
        author: '博主',
        category: '生活',
        tags: ['介绍', '博客'],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      },
      {
        id: 2,
        title: 'React 开发技巧分享',
        content: 'React 是一个非常强大的前端框架。今天我想分享一些实用的开发技巧...',
        author: '技术博主',
        category: '技术',
        tags: ['React', '前端', '技巧'],
        createdAt: new Date(Date.now() - 86400000).toISOString(),
        updatedAt: new Date(Date.now() - 86400000).toISOString()
      }
    ];
  })

  const [showForm, setShowForm] = useState(false)
  const [editingPost, setEditingPost] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('全部')
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    author: '',
    category: '',
    tags: ''
  })

  const categories = ['全部', '技术', '生活', '旅行', '美食', '学习']

  useEffect(() => {
    localStorage.setItem('blogPosts', JSON.stringify(posts));
  }, [posts])

  const resetForm = () => {
    setFormData({
      title: '',
      content: '',
      author: '',
      category: '',
      tags: ''
    })
    setEditingPost(null)
    setShowForm(false)
  }

  const handleSubmit = (e) => {
    e.preventDefault()

    if (!formData.title.trim() || !formData.content.trim()) {
      alert('请填写标题和内容')
      return
    }

    const postData = {
      title: formData.title.trim(),
      content: formData.content.trim(),
      author: formData.author.trim() || '匿名',
      category: formData.category || '未分类',
      tags: formData.tags.split(',').map(tag => tag.trim()).filter(tag => tag),
      createdAt: editingPost ? editingPost.createdAt : new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }

    if (editingPost) {
      setPosts(posts.map(post =>
        post.id === editingPost.id
          ? { ...post, ...postData }
          : post
      ))
    } else {
      const newPost = {
        id: Date.now(),
        ...postData
      }
      setPosts([newPost, ...posts])
    }

    resetForm()
  }

  const startEdit = (post) => {
    setEditingPost(post)
    setFormData({
      title: post.title,
      content: post.content,
      author: post.author,
      category: post.category,
      tags: post.tags.join(', ')
    })
    setShowForm(true)
  }

  const deletePost = (id) => {
    if (window.confirm('确定要删除这篇文章吗？')) {
      setPosts(posts.filter(post => post.id !== id))
    }
  }

  const filteredPosts = posts.filter(post => {
    const matchesSearch = post.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         post.content.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = selectedCategory === '全部' || post.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const truncateContent = (content, maxLength = 150) => {
    return content.length > maxLength
      ? content.substring(0, maxLength) + '...'
      : content
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-500 to-purple-600 p-4">
      <div className="max-w-6xl mx-auto">
        {/* 头部 */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 mb-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">📝 我的博客</h1>
              <p className="text-white/80">分享知识与经验的地方</p>
            </div>
            <button
              onClick={() => setShowForm(true)}
              className="bg-green-500 hover:bg-green-600 text-white px-6 py-3 rounded-lg transition-colors duration-200 flex items-center gap-2"
            >
              <Plus size={20} />
              写文章
            </button>
          </div>

          {/* 搜索和过滤 */}
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/60" size={20} />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="搜索文章..."
                className="w-full pl-10 pr-4 py-3 bg-white/20 text-white placeholder-white/70 rounded-lg focus:outline-none focus:ring-2 focus:ring-white/50"
              />
            </div>

            <div className="flex items-center gap-2">
              <Filter className="text-white/60" size={20} />
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="bg-white/20 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-white/50"
              >
                {categories.map(category => (
                  <option key={category} value={category} className="text-gray-800">
                    {category}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* 文章表单 */}
        {showForm && (
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 mb-6">
            <h2 className="text-2xl font-bold text-white mb-6">
              {editingPost ? '编辑文章' : '写新文章'}
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-white/80 mb-2">标题</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({...formData, title: e.target.value})}
                  className="w-full px-4 py-3 bg-white/20 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-white/50"
                  placeholder="输入文章标题..."
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-white/80 mb-2">作者</label>
                  <input
                    type="text"
                    value={formData.author}
                    onChange={(e) => setFormData({...formData, author: e.target.value})}
                    className="w-full px-4 py-3 bg-white/20 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-white/50"
                    placeholder="作者姓名"
                  />
                </div>

                <div>
                  <label className="block text-white/80 mb-2">分类</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({...formData, category: e.target.value})}
                    className="w-full px-4 py-3 bg-white/20 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-white/50"
                  >
                    <option value="" className="text-gray-800">选择分类</option>
                    {categories.slice(1).map(category => (
                      <option key={category} value={category} className="text-gray-800">
                        {category}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-white/80 mb-2">标签</label>
                  <input
                    type="text"
                    value={formData.tags}
                    onChange={(e) => setFormData({...formData, tags: e.target.value})}
                    className="w-full px-4 py-3 bg-white/20 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-white/50"
                    placeholder="用逗号分隔标签"
                  />
                </div>
              </div>

              <div>
                <label className="block text-white/80 mb-2">内容</label>
                <textarea
                  value={formData.content}
                  onChange={(e) => setFormData({...formData, content: e.target.value})}
                  rows={8}
                  className="w-full px-4 py-3 bg-white/20 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-white/50 resize-none"
                  placeholder="写下你的文章内容..."
                />
              </div>

              <div className="flex gap-4">
                <button
                  type="submit"
                  className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg transition-colors duration-200"
                >
                  {editingPost ? '更新文章' : '发布文章'}
                </button>
                <button
                  type="button"
                  onClick={resetForm}
                  className="bg-gray-500 hover:bg-gray-600 text-white px-6 py-3 rounded-lg transition-colors duration-200"
                >
                  取消
                </button>
              </div>
            </form>
          </div>
        )}

        {/* 文章列表 */}
        <div className="grid gap-6">
          {filteredPosts.map(post => (
            <div key={post.id} className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-xl p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h2 className="text-2xl font-bold text-white mb-2">{post.title}</h2>
                  <div className="flex items-center gap-4 text-white/70 text-sm mb-3">
                    <div className="flex items-center gap-1">
                      <User size={16} />
                      {post.author}
                    </div>
                    <div className="flex items-center gap-1">
                      <Calendar size={16} />
                      {formatDate(post.createdAt)}
                    </div>
                    <div className="flex items-center gap-1">
                      <Tag size={16} />
                      {post.category}
                    </div>
                  </div>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => startEdit(post)}
                    className="text-blue-400 hover:text-blue-300 transition-colors p-2 hover:bg-white/10 rounded-lg"
                  >
                    <Edit size={18} />
                  </button>
                  <button
                    onClick={() => deletePost(post.id)}
                    className="text-red-400 hover:text-red-300 transition-colors p-2 hover:bg-white/10 rounded-lg"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>

              <p className="text-white/90 mb-4 leading-relaxed">
                {truncateContent(post.content)}
              </p>

              {post.tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {post.tags.map((tag, index) => (
                    <span
                      key={index}
                      className="bg-white/20 text-white px-3 py-1 rounded-full text-sm"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {filteredPosts.length === 0 && (
          <div className="text-center text-white/70 py-12">
            <p className="text-xl">没有找到匹配的文章</p>
            <p className="mt-2">试试调整搜索条件或写一篇新文章</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default App'''

    def _generate_charts_app(self, config: Dict[str, Any]) -> str:
        """生成图表展示应用组件"""
        return '''import React, { useState, useEffect } from 'react'
import { BarChart3, PieChart, LineChart, TrendingUp, Activity, Users, DollarSign } from 'lucide-react'

function App() {
  const [activeChart, setActiveChart] = useState('bar')
  const [data, setData] = useState({
    sales: [65, 59, 80, 81, 56, 55, 40],
    revenue: [1200, 1900, 3000, 5000, 2000, 3000, 4500],
    users: [120, 190, 300, 500, 200, 300, 450]
  })
  const [animationKey, setAnimationKey] = useState(0)

  useEffect(() => {
    // 模拟数据更新
    const interval = setInterval(() => {
      setData(prev => ({
        sales: prev.sales.map(val => Math.max(0, val + (Math.random() - 0.5) * 10)),
        revenue: prev.revenue.map(val => Math.max(0, val + (Math.random() - 0.5) * 500)),
        users: prev.users.map(val => Math.max(0, val + (Math.random() - 0.5) * 50))
      }))
      setAnimationKey(prev => prev + 1)
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月']

  const maxValue = (arr) => Math.max(...arr)
  const formatNumber = (num) => {
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'k'
    }
    return num.toString()
  }

  const BarChart = ({ data, color = '#3B82F6', title }) => {
    const maxVal = maxValue(data)
    return (
      <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6">
        <h3 className="text-white text-lg font-semibold mb-4">{title}</h3>
        <div className="flex items-end justify-between h-48 gap-2">
          {data.map((value, index) => (
            <div key={index} className="flex-1 flex flex-col items-center">
              <div
                className="w-full rounded-t transition-all duration-1000 ease-out"
                style={{
                  height: `${(value / maxVal) * 100}%`,
                  backgroundColor: color,
                  animation: `grow 1s ease-out ${index * 0.1}s both`
                }}
              />
              <span className="text-white/70 text-xs mt-2">{months[index]}</span>
              <span className="text-white text-sm font-medium">{formatNumber(Math.round(value))}</span>
            </div>
          ))}
        </div>
      </div>
    )
  }

  const LineChart = ({ data, color = '#10B981', title }) => {
    const maxVal = maxValue(data)
    const points = data.map((value, index) => {
      const x = (index / (data.length - 1)) * 100
      const y = 100 - (value / maxVal) * 100
      return `${x},${y}`
    }).join(' ')

    return (
      <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6">
        <h3 className="text-white text-lg font-semibold mb-4">{title}</h3>
        <div className="relative h-48">
          <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <defs>
              <linearGradient id={`gradient-${animationKey}`} x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor={color} />
                <stop offset="100%" stopColor={color} stopOpacity="0.6" />
              </linearGradient>
            </defs>
            <polyline
              fill="none"
              stroke={`url(#gradient-${animationKey})`}
              strokeWidth="2"
              points={points}
            />
            {data.map((value, index) => {
              const x = (index / (data.length - 1)) * 100
              const y = 100 - (value / maxVal) * 100
              return (
                <g key={index}>
                  <circle
                    cx={x}
                    cy={y}
                    r="3"
                    fill={color}
                    className="animate-pulse"
                  />
                  <text
                    x={x}
                    y={y - 8}
                    textAnchor="middle"
                    className="text-white text-xs font-medium"
                  >
                    {formatNumber(Math.round(value))}
                  </text>
                </g>
              )
            })}
          </svg>
          <div className="flex justify-between text-white/70 text-xs mt-2">
            {months.map(month => <span key={month}>{month}</span>)}
          </div>
        </div>
      </div>
    )
  }

  const PieChart = ({ data, colors, title }) => {
    const total = data.reduce((sum, val) => sum + val, 0)
    const percentages = data.map(val => ((val / total) * 100).toFixed(1))
    let currentAngle = 0

    return (
      <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6">
        <h3 className="text-white text-lg font-semibold mb-4">{title}</h3>
        <div className="flex items-center justify-center">
          <div className="relative w-32 h-32">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              {data.map((value, index) => {
                const angle = (value / total) * 360
                const x1 = 50 + 40 * Math.cos((currentAngle * Math.PI) / 180)
                const y1 = 50 + 40 * Math.sin((currentAngle * Math.PI) / 180)
                const x2 = 50 + 40 * Math.cos(((currentAngle + angle) * Math.PI) / 180)
                const y2 = 50 + 40 * Math.sin(((currentAngle + angle) * Math.PI) / 180)
                const largeArcFlag = angle > 180 ? 1 : 0

                const pathData = [
                  `M 50 50`,
                  `L ${x1} ${y1}`,
                  `A 40 40 0 ${largeArcFlag} 1 ${x2} ${y2}`,
                  `Z`
                ].join(' ')

                currentAngle += angle

                return (
                  <path
                    key={index}
                    d={pathData}
                    fill={colors[index % colors.length]}
                    className="transition-all duration-1000"
                  />
                )
              })}
            </svg>
          </div>
          <div className="ml-6 space-y-2">
            {data.map((value, index) => (
              <div key={index} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: colors[index % colors.length] }}
                />
                <span className="text-white text-sm">
                  {months[index]}: {percentages[index]}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const StatCard = ({ icon: Icon, title, value, change, color }) => (
    <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <Icon className={color} size={24} />
        <span className={`text-sm ${change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
          {change >= 0 ? '+' : ''}{change}%
        </span>
      </div>
      <h3 className="text-white/70 text-sm mb-1">{title}</h3>
      <p className="text-white text-2xl font-bold">{formatNumber(value)}</p>
    </div>
  )

  const totalSales = data.sales.reduce((sum, val) => sum + val, 0)
  const totalRevenue = data.revenue.reduce((sum, val) => sum + val, 0)
  const totalUsers = data.users.reduce((sum, val) => sum + val, 0)

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-purple-700 p-4">
      <div className="max-w-7xl mx-auto">
        {/* 头部 */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 mb-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">📊 数据仪表板</h1>
              <p className="text-white/80">实时数据分析和可视化</p>
            </div>
            <div className="flex items-center gap-2 text-white/70">
              <Activity size={20} />
              <span className="text-sm">实时更新</span>
            </div>
          </div>

          {/* 统计卡片 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <StatCard
              icon={TrendingUp}
              title="总销售额"
              value={totalSales}
              change={12.5}
              color="text-green-400"
            />
            <StatCard
              icon={DollarSign}
              title="总收入"
              value={totalRevenue}
              change={8.3}
              color="text-blue-400"
            />
            <StatCard
              icon={Users}
              title="活跃用户"
              value={totalUsers}
              change={-2.1}
              color="text-purple-400"
            />
          </div>
        </div>

        {/* 图表类型选择器 */}
        <div className="flex justify-center mb-6">
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-2 flex gap-2">
            {[
              { id: 'bar', icon: BarChart3, label: '柱状图' },
              { id: 'line', icon: LineChart, label: '折线图' },
              { id: 'pie', icon: PieChart, label: '饼图' }
            ].map(chart => (
              <button
                key={chart.id}
                onClick={() => setActiveChart(chart.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors duration-200 ${
                  activeChart === chart.id
                    ? 'bg-white/20 text-white'
                    : 'text-white/70 hover:text-white hover:bg-white/10'
                }`}
              >
                <chart.icon size={20} />
                {chart.label}
              </button>
            ))}
          </div>
        </div>

        {/* 图表展示区域 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {activeChart === 'bar' && (
            <>
              <BarChart data={data.sales} color="#3B82F6" title="月度销售数据" />
              <BarChart data={data.revenue} color="#10B981" title="月度收入数据" />
            </>
          )}

          {activeChart === 'line' && (
            <>
              <LineChart data={data.sales} color="#3B82F6" title="销售趋势" />
              <LineChart data={data.users} color="#8B5CF6" title="用户增长" />
            </>
          )}

          {activeChart === 'pie' && (
            <>
              <PieChart
                data={data.sales}
                colors={['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#84CC16']}
                title="销售分布"
              />
              <PieChart
                data={data.users}
                colors={['#8B5CF6', '#06B6D4', '#84CC16', '#F59E0B', '#EF4444', '#3B82F6', '#10B981']}
                title="用户分布"
              />
            </>
          )}
        </div>

        {/* 底部信息 */}
        <div className="mt-8 text-center text-white/60 text-sm">
          <p>数据每5秒自动更新 • 支持多种图表类型切换</p>
        </div>
      </div>

      <style jsx>{`
        @keyframes grow {
          from { height: 0; }
          to { height: var(--target-height); }
        }
      `}</style>
    </div>
  )
}

export default App'''

    def _generate_component(self, name: str, type: str, config: Dict[str, Any]) -> str:
        """生成额外的组件"""
        # 这里可以添加更多组件生成逻辑
        return f'''import React from 'react'

function {name}() {{
  return (
    <div className="{name.lower()}-component">
      <h2>{name} 组件</h2>
    </div>
  )
}}

export default {name}'''

    def _parse_html_to_project(self, html: str) -> Dict

    def _create_react_project(self, html_content: str, styles: list, scripts: list) -> Dict[str, str]:
        """创建完整的 React 项目结构"""
        files = {}

        # 1. package.json - 完整的 React 项目配置
        package_json = {
            "name": "pageforge-react-app",
            "version": "0.1.0",
            "private": true,
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "lint": "eslint . --ext js,jsx --report-unused-disable-directives --max-warnings 0",
                "preview": "vite preview"
            },
            "dependencies": {
                "react": "^19.0.0",
                "react-dom": "^19.0.0",
                "lucide-react": "^0.344.0"
            },
            "devDependencies": {
                "@types/react": "^19.0.0",
                "@types/react-dom": "^19.0.0",
                "@vitejs/plugin-react": "^4.2.1",
                "eslint": "^8.56.0",
                "eslint-plugin-react": "^7.34.0",
                "eslint-plugin-react-hooks": "^4.6.0",
                "eslint-plugin-react-refresh": "^0.4.5",
                "vite": "^5.1.0"
            }
        }
        files['package.json'] = json.dumps(package_json, indent=2, ensure_ascii=False)

        # 2. vite.config.js - Vite 配置
        files['vite.config.js'] = '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 6000
  }
})'''

        # 3. index.html - 入口 HTML 文件
        files['index.html'] = '''<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>PageForge React App</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>'''

        # 4. src/main.jsx - React 入口文件
        files['src/main.jsx'] = '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)'''

        # 5. src/index.css - 全局样式
        global_css = '''/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}

/* 添加提取的样式 */
'''
        if styles:
            global_css += '\n'.join(styles)
        files['src/index.css'] = global_css

        # 6. src/App.jsx - 主组件
        # 将 HTML 内容转换为 React 组件
        react_component = self._convert_html_to_react_component(html_content, scripts)
        files['src/App.jsx'] = react_component

        # 7. public/vite.svg - 占位图标（可选）
        files['public/vite.svg'] = '''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" aria-hidden="true" role="img" class="iconify iconify--logos" width="31.88" height="32" preserveAspectRatio="xMidYMid meet" viewBox="0 0 256 257"><defs><linearGradient id="IconifyId1813088fe1fbc01fb4764deg0" x1="-.828%" x2="57.632%" y1="7.652%" y2="78.411%"><stop offset="0%"></stop><stop offset="100%"></stop></linearGradient><linearGradient id="IconifyId1813088fe1fbc01fb4764deg1" x1="43.376%" x2="50.316%" y1="2.242%" y2="89.03%"><stop offset="0%"></stop><stop offset="100%"></stop></linearGradient></defs><path fill="url(#IconifyId1813088fe1fbc01fb4764deg0)" d="M255.153 37.938L134.897 252.976c-2.483 4.44-8.862 4.466-11.382.048L.325 37.958c-2.746-4.814 1.371-10.646 6.827-9.67l120.385 21.517a6.537 6.537 0 0 0 2.322-.004l114.786-22.053c5.438-.494 9.574 4.778 6.877 9.62Z"></path><path fill="url(#IconifyId1813088fe1fbc01fb4764deg1)" d="M185.432.063L96.44 17.501a3.268 3.268 0 0 0-2.634 3.014l-5.474 92.456a3.268 3.268 0 0 0 1.918 3.218l84.221 4.147c4.467.221 8.165-2.804 9.481-7.412l8.979-38.11a13.31 13.31 0 0 0-1.048-7.09l-10.112-19.029a13.31 13.31 0 0 0-7.683-6.785l-13.948-4.994Z"></path></svg>'''

        return files

    def _convert_html_to_react_component(self, html_content: str, scripts: list) -> str:
        """将 HTML 内容转换为 React 组件"""

        # 清理 HTML 内容
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # 转换 HTML 为 JSX
        jsx_content = self._html_to_jsx(soup)

        # 转换脚本为 React 状态和函数
        react_code = self._scripts_to_react_hooks(scripts)

        # 生成完整的 React 组件
        component_code = f'''import React, {{ {react_code['imports']} }} from 'react'

function App() {{
{react_code['state']}
{react_code['functions']}

  return (
    <div className="App">
{jsx_content}
    </div>
  )
}}

export default App'''

        return component_code

    def _html_to_jsx(self, soup) -> str:
        """将 HTML 转换为 JSX"""
        jsx_lines = []

        def process_element(element, indent=2):
            if element.name is None:  # 文本节点
                text = element.string.strip()
                if text:
                    return '  ' * indent + text
                return ''

            # 开始标签
            tag_name = element.name
            attrs = []

            # 处理属性
            for attr, value in element.attrs.items():
                if attr == 'class':
                    attrs.append(f'className="{value}"')
                elif attr == 'for':
                    attrs.append(f'htmlFor="{value}"')
                elif attr.startswith('on') and attr != 'onclick':
                    # 处理事件处理器
                    event_name = attr.lower().replace('on', 'on').lower()
                    attrs.append(f'{event_name}="{value}"')
                else:
                    attrs.append(f'{attr}="{value}"')

            attr_str = ' '.join(attrs)
            if attr_str:
                attr_str = ' ' + attr_str

            # 自闭合标签
            if len(element.contents) == 0 and tag_name in ['img', 'input', 'br', 'hr']:
                return '  ' * indent + f'<{tag_name}{attr_str} />'

            # 有内容的标签
            content_lines = []
            content_lines.append('  ' * indent + f'<{tag_name}{attr_str}>')

            for child in element.contents:
                child_jsx = process_element(child, indent + 1)
                if child_jsx:
                    content_lines.append(child_jsx)

            content_lines.append('  ' * indent + f'</{tag_name}>')

            return '\n'.join(content_lines)

        # 处理 body 内容
        if soup.body:
            for child in soup.body.contents:
                jsx = process_element(child)
                if jsx:
                    jsx_lines.append(jsx)
        else:
            jsx = process_element(soup)
            if jsx:
                jsx_lines.append(jsx)

        return '\n'.join(jsx_lines)

    def _scripts_to_react_hooks(self, scripts: list) -> Dict[str, str]:
        """将 JavaScript 脚本转换为 React Hooks"""

        if not scripts:
            return {
                'imports': '',
                'state': '',
                'functions': ''
            }

        combined_script = '\n'.join(scripts)

        # 简单的脚本分析
        has_localStorage = 'localStorage' in combined_script
        has_arrays = '[' in combined_script and ']' in combined_script
        has_functions = 'function' in combined_script

        imports = []
        state_code = []
        function_code = []

        # 添加必要的导入
        if has_localStorage or has_arrays:
            imports.append('useState')
        if has_localStorage:
            imports.append('useEffect')

        imports_str = ', '.join(imports) if imports else ''

        # 生成状态
        if has_localStorage and 'todos' in combined_script:
            state_code.append('  const [todos, setTodos] = useState(() => {')
            state_code.append('    const saved = localStorage.getItem("todos")')
            state_code.append('    return saved ? JSON.parse(saved) : []')
            state_code.append('  })')
            state_code.append('')

        # 生成函数
        if 'addTodo' in combined_script:
            function_code.append('  const addTodo = () => {')
            function_code.append('    if (newTodo.trim()) {')
            function_code.append('      const newTodos = [...todos, { id: Date.now(), text: newTodo, completed: false }]')
            function_code.append('      setTodos(newTodos)')
            function_code.append('      setNewTodo("")')
            function_code.append('    }')
            function_code.append('  }')
            function_code.append('')

        if 'toggleTodo' in combined_script:
            function_code.append('  const toggleTodo = (id) => {')
            function_code.append('    const newTodos = todos.map(todo =>')
            function_code.append('      todo.id === id ? { ...todo, completed: !todo.completed } : todo')
            function_code.append('    )')
            function_code.append('    setTodos(newTodos)')
            function_code.append('  }')
            function_code.append('')

        if 'deleteTodo' in combined_script:
            function_code.append('  const deleteTodo = (id) => {')
            function_code.append('    const newTodos = todos.filter(todo => todo.id !== id)')
            function_code.append('    setTodos(newTodos)')
            function_code.append('  }')
            function_code.append('')

        # 添加 useEffect 保存到 localStorage
        if has_localStorage:
            function_code.append('  useEffect(() => {')
            function_code.append('    localStorage.setItem("todos", JSON.stringify(todos))')
            function_code.append('  }, [todos])')
            function_code.append('')

        return {
            'imports': imports_str,
            'state': '\n'.join(state_code),
            'functions': '\n'.join(function_code)
        }

    def create_project(self, session_id: str, version: int, project_config: Dict[str, Any] = None) -> Dict[str, str]:
        """为指定会话和版本创建完整的 React 项目"""
        # 如果没有提供配置，创建默认的 React 项目
        if project_config is None:
            project_config = self._get_default_react_config()

        # 根据配置创建 React 项目文件
        files = self._create_react_project_from_config(project_config)

        # 创建项目目录
        project_dir = self._get_project_dir(session_id, version)
        project_dir.mkdir(parents=True, exist_ok=True)

        # 写入文件
        for file_path, content in files.items():
            full_path = project_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')

        return {
            "project_path": str(project_dir),
            "files": list(files.keys()),
            "status": "created",
            "config": project_config
        }

    def _get_default_react_config(self) -> Dict[str, Any]:
        """获取默认的 React 项目配置"""
        return {
            "name": "pageforge-react-app",
            "type": "react",
            "framework": "vite",
            "dependencies": ["react", "react-dom", "lucide-react"],
            "dev_dependencies": ["@vitejs/plugin-react", "@types/react", "@types/react-dom", "vite"],
            "template": "counter",  # counter, todo, calculator 等
            "features": ["hooks", "localStorage", "responsive"]
        }

    def create_project_from_template(self, session_id: str, version: int, template_name: str) -> Dict[str, str]:
        """从模板创建 React 项目"""
        templates = {
            "counter": self._get_counter_template_config(),
            "todo": self._get_todo_template_config(),
            "calculator": self._get_calculator_template_config(),
            "weather": self._get_weather_template_config(),
            "chat": self._get_chat_template_config(),
            "blog": self._get_blog_template_config(),
            "charts": self._get_charts_template_config()
        }

        if template_name not in templates:
            raise HTTPException(status_code=400, detail=f"模板 '{template_name}' 不存在")

        return self.create_project(session_id, version, templates[template_name])

    def _get_counter_template_config(self) -> Dict[str, Any]:
        """计数器模板配置"""
        return {
            "name": "counter-app",
            "type": "react",
            "framework": "vite",
            "template": "counter",
            "description": "一个简单的计数器应用",
            "dependencies": ["react", "react-dom"],
            "dev_dependencies": ["@vitejs/plugin-react", "@types/react", "@types/react-dom", "vite"],
            "features": ["hooks", "localStorage", "responsive"],
            "components": {
                "App": "counter",
                "Counter": "component"
            }
        }

    def _get_todo_template_config(self) -> Dict[str, Any]:
        """待办事项模板配置"""
        return {
            "name": "todo-app",
            "type": "react",
            "framework": "vite",
            "template": "todo",
            "description": "功能完整的待办事项管理应用",
            "dependencies": ["react", "react-dom", "lucide-react"],
            "dev_dependencies": ["@vitejs/plugin-react", "@types/react", "@types/react-dom", "vite"],
            "features": ["hooks", "localStorage", "responsive", "filtering"],
            "components": {
                "App": "todo",
                "TodoList": "component",
                "TodoItem": "component",
                "TodoForm": "component"
            }
        }

    def _get_calculator_template_config(self) -> Dict[str, Any]:
        """计算器模板配置"""
        return {
            "name": "calculator-app",
            "type": "react",
            "framework": "vite",
            "template": "calculator",
            "description": "功能完整的计算器应用",
            "dependencies": ["react", "react-dom"],
            "dev_dependencies": ["@vitejs/plugin-react", "@types/react", "@types/react-dom", "vite"],
            "features": ["hooks", "responsive", "keyboard-support"],
            "components": {
                "App": "calculator",
                "Display": "component",
                "Button": "component",
                "ButtonGrid": "component"
            }
        }

    def _get_weather_template_config(self) -> Dict[str, Any]:
        """天气应用模板配置"""
        return {
            "name": "weather-app",
            "type": "react",
            "framework": "vite",
            "template": "weather",
            "description": "实时天气查询应用",
            "dependencies": ["react", "react-dom", "lucide-react"],
            "dev_dependencies": ["@vitejs/plugin-react", "@types/react", "@types/react-dom", "vite"],
            "features": ["hooks", "localStorage", "responsive", "search"],
            "components": {
                "App": "weather",
                "WeatherCard": "component",
                "SearchBox": "component",
                "WeatherDetails": "component"
            }
        }

    def _get_chat_template_config(self) -> Dict[str, Any]:
        """聊天应用模板配置"""
        return {
            "name": "chat-app",
            "type": "react",
            "framework": "vite",
            "template": "chat",
            "description": "实时聊天应用",
            "dependencies": ["react", "react-dom", "lucide-react"],
            "dev_dependencies": ["@vitejs/plugin-react", "@types/react", "@types/react-dom", "vite"],
            "features": ["hooks", "localStorage", "responsive", "real-time"],
            "components": {
                "App": "chat",
                "MessageList": "component",
                "MessageInput": "component",
                "ChatHeader": "component"
            }
        }

    def _get_blog_template_config(self) -> Dict[str, Any]:
        """博客系统模板配置"""
        return {
            "name": "blog-app",
            "type": "react",
            "framework": "vite",
            "template": "blog",
            "description": "功能完整的博客系统",
            "dependencies": ["react", "react-dom", "lucide-react"],
            "dev_dependencies": ["@vitejs/plugin-react", "@types/react", "@types/react-dom", "vite"],
            "features": ["hooks", "localStorage", "responsive", "crud", "search"],
            "components": {
                "App": "blog",
                "PostList": "component",
                "PostForm": "component",
                "PostItem": "component",
                "SearchBar": "component"
            }
        }

    def _get_charts_template_config(self) -> Dict[str, Any]:
        """图表展示模板配置"""
        return {
            "name": "charts-app",
            "type": "react",
            "framework": "vite",
            "template": "charts",
            "description": "数据可视化图表应用",
            "dependencies": ["react", "react-dom", "lucide-react"],
            "dev_dependencies": ["@vitejs/plugin-react", "@types/react", "@types/react-dom", "vite"],
            "features": ["hooks", "responsive", "animation", "real-time-data"],
            "components": {
                "App": "charts",
                "BarChart": "component",
                "LineChart": "component",
                "PieChart": "component",
                "StatCard": "component"
            }
        }

    def get_project_status(self, session_id: str, version: int) -> Dict[str, any]:
        """获取项目状态"""
        project_dir = self._get_project_dir(session_id, version)

        if not project_dir.exists():
            return {
                "status": "not_found",
                "message": "Project not created yet"
            }

        # 检查必要文件
        required_files = ['index.html', 'package.json', 'src/style.css', 'src/main.js']
        existing_files = []
        missing_files = []

        for file in required_files:
            if (project_dir / file).exists():
                existing_files.append(file)
            else:
                missing_files.append(file)

        # 检查 node_modules
        has_node_modules = (project_dir / 'node_modules').exists()

        # 检查 package.json
        package_json_path = project_dir / 'package.json'
        if package_json_path.exists():
            try:
                package_data = json.loads(package_json_path.read_text())
                dependencies = package_data.get('dependencies', {})
                dev_dependencies = package_data.get('devDependencies', {})
            except json.JSONDecodeError:
                dependencies = {}
                dev_dependencies = {}
        else:
            dependencies = {}
            dev_dependencies = {}

        return {
            "status": "ready" if has_node_modules else "created",
            "project_path": str(project_dir),
            "existing_files": existing_files,
            "missing_files": missing_files,
            "has_node_modules": has_node_modules,
            "dependencies": dependencies,
            "dev_dependencies": dev_dependencies
        }

    def install_dependencies(self, session_id: str, version: int) -> Dict[str, any]:
        """安装项目依赖"""
        project_dir = self._get_project_dir(session_id, version)

        if not project_dir.exists():
            raise HTTPException(status_code=404, detail="Project not found")

        package_json_path = project_dir / 'package.json'
        if not package_json_path.exists():
            raise HTTPException(status_code=400, detail="package.json not found")

        try:
            # 安装依赖
            result = subprocess.run(
                ['npm', 'install'],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )

            if result.returncode != 0:
                return {
                    "status": "error",
                    "message": "依赖安装失败",
                    "error": result.stderr,
                    "stdout": result.stdout
                }

            return {
                "status": "success",
                "message": "依赖安装成功",
                "stdout": result.stdout
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": "依赖安装超时",
                "error": "安装过程超过5分钟"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": "依赖安装异常",
                "error": str(e)
            }

    def start_dev_server(self, session_id: str, version: int) -> Dict[str, any]:
        """启动开发服务器"""
        project_dir = self._get_project_dir(session_id, version)

        if not project_dir.exists():
            raise HTTPException(status_code=404, detail="Project not found")

        # 检查 node_modules 是否存在
        if not (project_dir / 'node_modules').exists():
            return {
                "status": "error",
                "message": "请先安装依赖"
            }

        try:
            # 启动开发服务器
            process = subprocess.Popen(
                ['npm', 'run', 'dev'],
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # 等待几秒钟检查是否成功启动
            import time
            time.sleep(3)

            if process.poll() is None:
                # 进程仍在运行，说明启动成功
                return {
                    "status": "success",
                    "message": "开发服务器启动成功",
                    "port": 6000,  # Vite 端口
                    "url": f"http://localhost:6000",
                    "pid": process.pid
                }
            else:
                # 进程已退出，读取错误信息
                stdout, stderr = process.communicate()
                return {
                    "status": "error",
                    "message": "开发服务器启动失败",
                    "error": stderr,
                    "stdout": stdout
                }

        except Exception as e:
            return {
                "status": "error",
                "message": "启动异常",
                "error": str(e)
            }

    def get_project_files(self, session_id: str, version: int) -> Dict[str, any]:
        """获取项目文件列表和内容"""
        project_dir = self._get_project_dir(session_id, version)

        if not project_dir.exists():
            raise HTTPException(status_code=404, detail="Project not found")

        files = {}
        for file_path in project_dir.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(project_dir)
                try:
                    content = file_path.read_text(encoding='utf-8')
                    files[str(relative_path)] = {
                        "content": content,
                        "size": file_path.stat().st_size,
                        "modified": file_path.stat().st_mtime
                    }
                except UnicodeDecodeError:
                    # 二进制文件跳过
                    files[str(relative_path)] = {
                        "content": "[Binary file]",
                        "size": file_path.stat().st_size,
                        "modified": file_path.stat().st_mtime,
                        "is_binary": True
                    }

        return {
            "project_path": str(project_dir),
            "files": files
        }

    def cleanup_project(self, session_id: str, version: int) -> Dict[str, any]:
        """清理项目文件"""
        project_dir = self._get_project_dir(session_id, version)

        if project_dir.exists():
            try:
                shutil.rmtree(project_dir)
                return {
                    "status": "success",
                    "message": "项目清理完成"
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": "清理失败",
                    "error": str(e)
                }
        else:
            return {
                "status": "not_found",
                "message": "项目不存在"
            }

    def cleanup_session(self, session_id: str) -> Dict[str, any]:
        """清理会话的所有项目"""
        session_dir = self.temp_dir / session_id

        if session_dir.exists():
            try:
                shutil.rmtree(session_dir)
                return {
                    "status": "success",
                    "message": "会话清理完成"
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": "清理失败",
                    "error": str(e)
                }
        else:
            return {
                "status": "not_found",
                "message": "会话不存在"
            }