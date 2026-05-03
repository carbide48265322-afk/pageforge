import { useState } from "react";
import { Play, Code, Globe, Terminal, Check, AlertCircle } from "lucide-react";

/**
 * WebContainer 功能演示组件
 * 展示 WebContainer 的核心功能和使用方法
 */
export function WebContainerDemo() {
    const [activeTab, setActiveTab] = useState<'features' | 'usage' | 'examples'>('features');

    const features = [
        {
            icon: <Globe className="w-6 h-6" />,
            title: "完整浏览器环境",
            description: "在浏览器中运行完整的 Node.js 环境，支持 npm 包管理和构建工具"
        },
        {
            icon: <Code className="w-6 h-6" />,
            title: "实时开发体验",
            description: "自动启动开发服务器，支持热重载和实时预览"
        },
        {
            icon: <Terminal className="w-6 h-6" />,
            title: "控制台监控",
            description: "实时查看应用日志、错误信息和调试输出"
        }
    ];

    const usageSteps = [
        {
            step: 1,
            title: "生成页面",
            description: "通过 AI 对话生成 HTML 页面内容",
            icon: <Code className="w-5 h-5" />
        },
        {
            step: 2,
            title: "启动环境",
            description: "切换到运行环境标签，点击启动按钮",
            icon: <Play className="w-5 h-5" />
        },
        {
            step: 3,
            title: "等待初始化",
            description: "系统自动完成依赖安装和服务器启动",
            icon: <Check className="w-5 h-5" />
        },
        {
            step: 4,
            title: "交互测试",
            description: "在完整环境中测试页面功能和交互",
            icon: <Globe className="w-5 h-5" />
        }
    ];

    const examples = [
        {
            title: "计数器应用",
            description: "包含增加、减少、重置功能的交互式计数器",
            features: ["JavaScript 交互", "CSS 动画", "响应式设计"],
            complexity: "简单"
        },
        {
            title: "待办事项列表",
            description: "支持添加、删除、标记完成的任务管理应用",
            features: ["本地存储", "状态管理", "数据持久化"],
            complexity: "中等"
        },
        {
            title: "数据可视化",
            description: "使用 Chart.js 展示数据的图表应用",
            features: ["第三方库", "图表渲染", "数据处理"],
            complexity: "高级"
        }
    ];

    return (
        <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
            <div className="text-center mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">
                    WebContainer 功能演示
                </h1>
                <p className="text-gray-600">
                    在浏览器中运行完整的开发环境，让 AI 生成的页面真正"活"起来
                </p>
            </div>

            {/* 标签导航 */}
            <div className="flex border-b border-gray-200 mb-6">
                {[
                    { key: 'features', label: '功能特性', icon: <Globe className="w-4 h-4" /> },
                    { key: 'usage', label: '使用方法', icon: <Play className="w-4 h-4" /> },
                    { key: 'examples', label: '示例项目', icon: <Code className="w-4 h-4" /> }
                ].map((tab) => (
                    <button
                        key={tab.key}
                        onClick={() => setActiveTab(tab.key as any)}
                        className={`flex items-center gap-2 px-4 py-2 border-b-2 font-medium text-sm ${
                            activeTab === tab.key
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700'
                        }`}
                    >
                        {tab.icon}
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* 功能特性 */}
            {activeTab === 'features' && (
                <div className="grid gap-6 md:grid-cols-3">
                    {features.map((feature, index) => (
                        <div key={index} className="p-6 border border-gray-200 rounded-lg">
                            <div className="text-blue-600 mb-3">{feature.icon}</div>
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">
                                {feature.title}
                            </h3>
                            <p className="text-gray-600 text-sm">
                                {feature.description}
                            </p>
                        </div>
                    ))}
                </div>
            )}

            {/* 使用方法 */}
            {activeTab === 'usage' && (
                <div className="space-y-6">
                    {usageSteps.map((step, index) => (
                        <div key={index} className="flex items-start gap-4">
                            <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-semibold">
                                {step.step}
                            </div>
                            <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                    {step.icon}
                                    <h3 className="text-lg font-semibold text-gray-900">
                                        {step.title}
                                    </h3>
                                </div>
                                <p className="text-gray-600">{step.description}</p>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* 示例项目 */}
            {activeTab === 'examples' && (
                <div className="grid gap-6 md:grid-cols-3">
                    {examples.map((example, index) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-6">
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="text-lg font-semibold text-gray-900">
                                    {example.title}
                                </h3>
                                <span className={`px-2 py-1 text-xs rounded ${
                                    example.complexity === '简单' ? 'bg-green-100 text-green-800' :
                                    example.complexity === '中等' ? 'bg-yellow-100 text-yellow-800' :
                                    'bg-red-100 text-red-800'
                                }`}>
                                    {example.complexity}
                                </span>
                            </div>
                            <p className="text-gray-600 text-sm mb-4">
                                {example.description}
                            </p>
                            <div className="space-y-2">
                                {example.features.map((feature, featureIndex) => (
                                    <div key={featureIndex} className="flex items-center gap-2 text-sm text-gray-600">
                                        <Check className="w-4 h-4 text-green-500" />
                                        {feature}
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* 注意事项 */}
            <div className="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-start gap-2">
                    <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                    <div>
                        <h4 className="font-semibold text-yellow-800 mb-1">注意事项</h4>
                        <ul className="text-sm text-yellow-700 space-y-1">
                            <li>• WebContainer 启动需要 30-60 秒，请耐心等待</li>
                            <li>• 使用完毕后及时停止环境以释放内存资源</li>
                            <li>• 复杂的第三方库可能需要额外的配置时间</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
}