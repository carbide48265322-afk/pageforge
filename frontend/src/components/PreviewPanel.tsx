import { useEffect, useState } from "react";
import { X, Monitor, Tablet, Smartphone, Copy, Download, Check, Loader2 } from "lucide-react";
import { Light as SyntaxHighlighter } from "react-syntax-highlighter";
import xml from "react-syntax-highlighter/dist/esm/languages/hljs/xml";
import github from "react-syntax-highlighter/dist/esm/styles/hljs/github";
// 注册语言（xml 包含 html 别名）
SyntaxHighlighter.registerLanguage("xml", xml);
SyntaxHighlighter.registerLanguage("html", xml);

/** 工作流阶段类型 */
export type WorkflowStage = {
    stage: string;
    label: string;
    color: string;
};

/** 预览面板的 props */
interface PreviewPanelProps {
    /** HTML 内容 */
    html: string;
    /** 流式输出的 HTML（生成过程中源码视图实时展示） */
    streamingHtml: string;
    /** 是否展示预览面板 */
    isOpen: boolean;
    /** 关闭预览面板回调 */
    onClose: () => void;
    /** 当前工作流阶段 */
    workflowStage?: WorkflowStage | null;
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
 * 预览面板组件
 * 使用 iframe sandbox 渲染生成的 HTML
 * 支持预览/源码切换、响应式尺寸切换、收起/展开
 * 使用 CSS display 切换避免 iframe 重复加载
 */
export function PreviewPanel({ html, streamingHtml, isOpen, onClose, workflowStage }: PreviewPanelProps) {
    const [viewMode, setViewMode] = useState<"preview" | "source">("preview");
    const [size, setSize] = useState<ResponsiveSize>("desktop");
    // 新增 state 控制复制成功提示
    const [copied, setCopied] = useState(false);

    // 动画控制：mounted 控制是否渲染 DOM，visible 控制动画状态
    const [mounted, setMounted] = useState(false);
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        if (isOpen) {
            setMounted(true);
            // 双 rAF 确保浏览器先渲染初始状态，再触发过渡动画
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
    const displayHtml = streamingHtml || html;

    // 未打开时不渲染
    if (!isOpen) return null;

    return (
        <div
            className={`flex flex-col h-full bg-white transition-all duration-300 ease-in-out ${visible ? "opacity-100 translate-x-0" : "opacity-0 translate-x-4"
                }`}
            onTransitionEnd={handleTransitionEnd}
        >            {/* 顶部工具栏 */}
            <div className="flex items-center justify-between border-b border-gray-200 px-4 py-2">
                <div className="flex items-center">
                    {/* 工作流阶段显示 */}
                    {workflowStage && (
                        <div className="mr-4">
                            <div className={`flex items-center gap-2 text-xs font-medium ${workflowStage.color}`}>
                                <Loader2 size={12} className="animate-spin" />
                                <span>{workflowStage.label}</span>
                            </div>
                        </div>
                    )}
                    {/* 视图模式切换 */}
                    <div className="flex items-center gap-1 mr-4">
                        <button
                            onClick={() => setViewMode("preview")}
                            className={`px-2 py-1 text-xs rounded transition-colors ${viewMode === "preview"
                                ? "bg-gray-100 text-gray-900 font-medium"
                                : "text-gray-400 hover:text-gray-600"
                                }`}
                        >
                            预览
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

                    {/* 响应式尺寸切换（仅预览模式可用） */}
                    {viewMode === "preview" && (
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
                        {/* 预览层：CSS display 切换，避免 iframe 重复加载 */}
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
                                    {/*
                                        sandbox="allow-scripts" 允许页面内 JS 执行
                                        不加 allow-same-origin 防止跨沙箱通信
                                    */}
                                    <iframe
                                        srcDoc={displayHtml}
                                        sandbox="allow-scripts"
                                        className="w-full h-full border-0"
                                        title="页面预览"
                                    />
                                </div>
                            </div>
                        </div>
                        {/* 源码层：只读 HTML 文本 */}
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