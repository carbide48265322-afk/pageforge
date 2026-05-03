import { useEffect, useState, useRef } from "react";
import { X, Monitor, Tablet, Smartphone, Copy, Download, Check, Play, Square, RefreshCw, Terminal, Globe } from "lucide-react";
import { Light as SyntaxHighlighter } from "react-syntax-highlighter";
import xml from "react-syntax-highlighter/dist/esm/languages/hljs/xml";
import github from "react-syntax-highlighter/dist/esm/styles/hljs/github";
import { useWebContainer } from "../services/webcontainer_api";
import { useState, useEffect } from "react";

// 注册语言（xml 包含 html 别名）
SyntaxHighlighter.registerLanguage("xml", xml);
SyntaxHighlighter.registerLanguage("html", xml);

/** WebContainer 预览面板的 props */
interface WebContainerPanelProps {
    /** HTML 内容 */
    html: string;
    /** 流式输出的 HTML（生成过程中源码视图实时展示） */
    streamingHtml: string;
    /** 是否展示预览面板 */
    isOpen: boolean;
    /** 关闭预览面板回调 */
    onClose: () => void;
    /** 当前会话 ID */
    sessionId?: string;
    /** 最新版本号 */
    latestVersion?: number;
}

/** 响应式尺寸类型 */
type ResponsiveSize = "desktop" | "tablet" | "mobile";

/** 各尺寸对应的宽度 */
const SIZE_WIDTHS: Record<ResponsiveSize, string> = {
    desktop: "100%",
    tablet: "768px",
    mobile: "375px",
};

/**
 * WebContainer 预览面板组件
 * 使用 WebContainer 在浏览器中运行生成的项目
 * 支持预览/源码切换、响应式尺寸切换、运行/停止控制
 */
export function WebContainerPanel({ html, streamingHtml, isOpen, onClose }: WebContainerPanelProps) {
    const [viewMode, setViewMode] = useState<"preview" | "source" | "webcontainer">("preview");
    const [size, setSize] = useState<ResponsiveSize>("desktop");
    const [copied, setCopied] = useState(false);
    const [isRunning, setIsRunning] = useState(false);
    const [isStarting, setIsStarting] = useState(false);
    const [containerStatus, setContainerStatus] = useState<string>("未初始化");
    const [consoleOutput, setConsoleOutput] = useState<string[]>([]);
    const [showConsole, setShowConsole] = useState(false);
    const [currentSessionId, setCurrentSessionId] = useState<string>("");
    const [currentVersion, setCurrentVersion] = useState<number>(1);

    // 动画控制
    const [mounted, setMounted] = useState(false);
    const [visible, setVisible] = useState(false);

    // WebContainer 相关
    const webContainerRef = useRef<HTMLDivElement>(null);
    const {
        state: containerState,
        isReady: isContainerReady,
        serverUrl,
        initializeProject,
        refreshStatus,
        installDependencies,
        startServer,
        cleanup,
    } = useWebContainer();


    useEffect(() => {
        if (isOpen) {
            setMounted(true);
            requestAnimationFrame(() => {
                requestAnimationFrame(() => setVisible(true));
            });
        } else {
            setVisible(false);
        }
    }, [isOpen]);

    // 有流式内容时自动切换到源码视图
    useEffect(() => {
        if (streamingHtml) {
            setViewMode("source");
        }
    }, [streamingHtml]);


    /** 退出动画完成后卸载 DOM */
    const handleTransitionEnd = () => {
        if (!isOpen) setMounted(false);
    };

    if (!mounted) return null;

    /** 复制 HTML 源码到剪贴板 */
    const handleCopy = async () => {
        if (!html) return;
        await navigator.clipboard.writeText(html);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    /** 下载 HTML 文件 */
    const handleDownload = () => {
        if (!html) return;
        const blob = new Blob([html], { type: "text/html" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "page.html";
        a.click();
        URL.revokeObjectURL(url);
    };

    /** 启动 WebContainer */
    const handleStartContainer = async () => {
        if (!webContainerRef.current || !sessionId) return;

        setIsStarting(true);
        setContainerStatus("正在初始化...");
        setConsoleOutput([]);

        try {
            // 获取最新版本号
            const version = latestVersion || 1;
            setCurrentSessionId(sessionId);
            setCurrentVersion(version);

            // 初始化项目（模板由后端决定）
            if (!html) {
                throw new Error("HTML 内容为空");
            }
            await initializeProject(sessionId, version);
            setContainerStatus("项目初始化完成");
            setConsoleOutput(prev => [...prev, "✓ 项目加载成功"]);

            setIsRunning(true);
            setViewMode("webcontainer");

        } catch (error) {
            console.error("启动 WebContainer 失败:", error);
            setContainerStatus(`启动失败: ${error}`);
            setConsoleOutput(prev => [...prev, `✗ 启动失败: ${error}`]);
        } finally {
            setIsStarting(false);
        }
    };

    /** 停止 WebContainer */
    const handleStopContainer = async () => {
        try {
            await cleanup();
            setIsRunning(false);
            setContainerStatus("已停止");
            setConsoleOutput(prev => [...prev, "✓ WebContainer 已停止"]);
        } catch (error) {
            console.error("停止 WebContainer 失败:", error);
            setConsoleOutput(prev => [...prev, `✗ 停止失败: ${error}`]);
        }
    };

    /** 刷新 WebContainer */
    const handleRefreshContainer = async () => {
        if (isRunning) {
            await handleStopContainer();
        }
        await handleStartContainer();
    };

    const displayHtml = streamingHtml || html;

    if (!isOpen) return null;

    return (
        <div
            className={`flex flex-col h-full bg-white transition-all duration-300 ease-in-out ${visible ? "opacity-100 translate-x-0" : "opacity-0 translate-x-4"
                }`}
            onTransitionEnd={handleTransitionEnd}
        >
            {/* 顶部工具栏 */}
            <div className="flex items-center justify-between border-b border-gray-200 px-4 py-2">
                <div className="flex items-center">
                    {/* 视图模式切换 */}
                    <div className="flex items-center gap-1 mr-4">
                        <button
                            onClick={() => setViewMode("preview")}
                            className={`px-2 py-1 text-xs rounded transition-colors ${viewMode === "preview"
                                    ? "bg-gray-100 text-gray-900 font-medium"
                                    : "text-gray-400 hover:text-gray-600"
                                }`}
                        >
                            <Globe size={12} className="inline mr-1" />
                            预览
                        </button>
                        <button
                            onClick={() => setViewMode("webcontainer")}
                            className={`px-2 py-1 text-xs rounded transition-colors ${viewMode === "webcontainer"
                                    ? "bg-green-100 text-green-700 font-medium"
                                    : "text-gray-400 hover:text-gray-600"
                                }`}
                        >
                            <Terminal size={12} className="inline mr-1" />
                            运行环境
                        </button>
                        <button
                            onClick={() => setViewMode("source")}
                            className={`px-2 py-1 text-xs rounded transition-colors ${viewMode === "source"
                                    ? "bg-gray-100 text-gray-900 font-medium"
                                    : "text-gray-400 hover:text-gray-600"
                                }`}
                        >
                            源码
                        </button>
                    </div>

                    {/* WebContainer 控制 */}
                    {viewMode === "webcontainer" && (
                        <div className="flex items-center gap-2 mr-4">
                            {!isRunning ? (
                                <button
                                    onClick={handleStartContainer}
                                    disabled={isStarting || !html}
                                    className="flex items-center gap-1 px-2 py-1 text-xs bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <Play size={12} />
                                    {isStarting ? "启动中..." : "启动环境"}
                                </button>
                            ) : (
                                <div className="flex items-center gap-1">
                                    <button
                                        onClick={handleStopContainer}
                                        className="flex items-center gap-1 px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600"
                                    >
                                        <Square size={12} />
                                        停止
                                    </button>
                                    <button
                                        onClick={handleRefreshContainer}
                                        className="flex items-center gap-1 px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
                                    >
                                        <RefreshCw size={12} />
                                        重启
                                    </button>
                                </div>
                            )}

                            {/* 控制台切换 */}
                            <button
                                onClick={() => setShowConsole(!showConsole)}
                                className={`flex items-center gap-1 px-2 py-1 text-xs rounded transition-colors ${showConsole
                                        ? "bg-gray-100 text-gray-900"
                                        : "text-gray-400 hover:text-gray-600"
                                    }`}
                            >
                                <Terminal size={12} />
                                控制台
                            </button>
                        </div>
                    )}

                    {/* 响应式尺寸切换（仅预览模式可用） */}
                    {(viewMode === "preview" || viewMode === "webcontainer") && (
                        <div className="flex items-center gap-1">
                            <button
                                onClick={() => setSize("desktop")}
                                className={`p-1.5 rounded transition-colors ${size === "desktop"
                                        ? "bg-gray-100 text-gray-900"
                                        : "text-gray-400 hover:text-gray-600"
                                    }`}
                                title="桌面端"
                            >
                                <Monitor size={16} />
                            </button>
                            <button
                                onClick={() => setSize("tablet")}
                                className={`p-1.5 rounded transition-colors ${size === "tablet"
                                        ? "bg-gray-100 text-gray-900"
                                        : "text-gray-400 hover:text-gray-600"
                                    }`}
                                title="平板端"
                            >
                                <Tablet size={16} />
                            </button>
                            <button
                                onClick={() => setSize("mobile")}
                                className={`p-1.5 rounded transition-colors ${size === "mobile"
                                        ? "bg-gray-100 text-gray-900"
                                        : "text-gray-400 hover:text-gray-600"
                                    }`}
                                title="手机端"
                            >
                                <Smartphone size={16} />
                            </button>
                        </div>
                    )}
                </div>
                <div className="flex items-center gap-1">
                    {/* 复制按钮 */}
                    <button
                        onClick={handleCopy}
                        className="p-1.5 rounded text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                        title={copied ? "已复制" : "复制源码"}
                    >
                        {copied ? <Check size={16} className="text-green-500" /> : <Copy size={16} />}
                    </button>

                    {/* 下载按钮 */}
                    <button
                        onClick={handleDownload}
                        className="p-1.5 rounded text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                        title="下载 HTML"
                    >
                        <Download size={16} />
                    </button>
                    {/* 收起按钮 */}
                    <button
                        onClick={onClose}
                        className="p-1.5 rounded text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                        title="收起预览"
                    >
                        <X size={16} />
                    </button>
                </div>
            </div>

            {/* 内容区域 */}
            <div className="flex-1 overflow-auto bg-gray-100 p-4">
                {/* 空值提示 */}
                {!displayHtml || displayHtml.trim().length === 0 ? (
                    <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                        暂无预览内容
                    </div>
                ) : displayHtml.length > 2 * 1024 * 1024 ? (
                    /* 超过 2MB 提示 */
                    <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                        页面内容过大，请查看源码
                    </div>
                ) : (
                    <>
                        {/* 预览层：传统 iframe 预览 */}
                        <div
                            className="h-full"
                            style={{ display: viewMode === "preview" ? "block" : "none" }}
                        >
                            <div className="flex items-start justify-center h-full overflow-hidden">
                                <div
                                    className="bg-white shadow-lg rounded-lg overflow-hidden transition-all duration-300"
                                    style={{
                                        width: SIZE_WIDTHS[size],
                                        height: "100%",
                                    }}
                                >
                                    <iframe
                                        srcDoc={displayHtml}
                                        sandbox="allow-scripts"
                                        className="w-full h-full border-0"
                                        title="页面预览"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* WebContainer 运行环境层 */}
                        <div
                            className="h-full"
                            style={{ display: viewMode === "webcontainer" ? "flex" : "none" }}
                        >
                            <div className="flex-1 flex flex-col">
                                {/* 状态栏 */}
                                <div className="bg-gray-800 text-white p-2 text-xs">
                                    状态: {containerStatus}
                                    {isRunning && (
                                        <span className="ml-2 px-2 py-1 bg-green-600 rounded">
                                            运行中
                                        </span>
                                    )}
                                </div>

                                {/* WebContainer 容器 */}
                                <div
                                    className="flex-1 bg-white shadow-lg rounded-lg overflow-hidden"
                                    style={{
                                        width: SIZE_WIDTHS[size],
                                        height: "100%",
                                        margin: "0 auto"
                                    }}
                                >
                                    {isContainerReady && serverUrl ? (
                                        <iframe
                                            src={serverUrl}
                                            className="w-full h-full border-0"
                                            title="React 应用"
                                        />
                                    ) : (
                                        <div
                                            ref={webContainerRef}
                                            className="w-full h-full flex items-center justify-center bg-gray-50"
                                        >
                                            <div className="text-center text-gray-500">
                                                <div className="text-sm mb-2">
                                                    WebContainer
                                                </div>
                                                <div className="text-xs">
                                                    {containerStatus}
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* 控制台输出 */}
                            {showConsole && (
                                <div className="w-80 bg-gray-900 text-green-400 p-4 overflow-y-auto text-xs font-mono">
                                    <div className="mb-2 font-bold">控制台输出</div>
                                    <div className="space-y-1">
                                        {consoleOutput.map((line, index) => (
                                            <div key={index} className="whitespace-pre-wrap">
                                                {line}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* 源码层：HTML 语法高亮 */}
                        <div
                            className="h-full"
                            style={{ display: viewMode === "source" ? "block" : "none" }}
                        >
                            <SyntaxHighlighter
                                language="html"
                                style={github}
                                className="h-full !bg-white text-xs"
                                showLineNumbers
                            >
                                {displayHtml}
                            </SyntaxHighlighter>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}