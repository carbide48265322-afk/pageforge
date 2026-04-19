import { useState, useRef, useEffect } from "react";
import { Send, Square, ChevronDown } from "lucide-react";
import { MessageBubble } from "./MessageBubble";
import { ThinkingPanel } from "./ThinkingPanel";
import type { Message, ToolCall } from "../services/api";
import type { ThinkingStep } from "../hooks/useSSE";

/** ChatPanel 组件的 props */
interface ChatPanelProps {
    /** 消息列表 */
    messages: Message[];
    /** 是否正在加载 */
    isLoading: boolean;
    /** 思考步骤 */
    thinkingSteps: ThinkingStep[];
    /** 当前工具调用 */
    currentToolCall: ToolCall | null;
    /** 发送消息回调 */
    onSendMessage: (content: string) => void;
    /** 停止生成回调 */
    onStopGeneration: () => void;
}

/**
 * 聊天面板组件
 * 包含消息列表、思考过程展示、输入框和操作按钮
 * 使用 IntersectionObserver 实现智能滚动
 */
export function ChatPanel({
    messages,
    isLoading,
    thinkingSteps,
    currentToolCall,
    onSendMessage,
    onStopGeneration,
}: ChatPanelProps) {
    const [input, setInput] = useState("");
    const [isAtBottom, setIsAtBottom] = useState(true);
    // 新增 state 追踪 IME 组合状态
    const [isComposing, setIsComposing] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const scrollContainerRef = useRef<HTMLDivElement>(null);

    // 用 IntersectionObserver 监测锚点元素是否可见
    // 可见 = 用户在底部，不可见 = 用户上滑查看历史
    useEffect(() => {
        const container = scrollContainerRef.current;
        if (!container) return;

        const observer = new IntersectionObserver(
            ([entry]) => {
                setIsAtBottom(entry.isIntersecting);
            },
            {
                root: container,
                threshold: 0,
            },
        );

        const anchor = messagesEndRef.current;
        if (anchor) {
            observer.observe(anchor);
        }

        return () => observer.disconnect();
    }, []);

    // 智能滚动：仅在用户处于底部时自动跟随
    useEffect(() => {
        if (isAtBottom) {
            messagesEndRef.current?.scrollIntoView({ behavior: "instant" });
        }
    }, [messages, thinkingSteps, currentToolCall, isAtBottom]);

    /** 提交消息 */
    const handleSubmit = () => {
        const trimmed = input.trim();
        if (!trimmed || isLoading) return;
        onSendMessage(trimmed);
        setInput("");
    };

    /** 回车发送（Shift+Enter 换行） */
    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey && !isComposing) {
            e.preventDefault();
            handleSubmit();
        }
    };

    return (
        <div className="flex flex-col h-full">
            {/* 消息列表区域 */}
            <div
                ref={scrollContainerRef}
                className="flex-1 overflow-y-auto px-4 py-4"
            >
                {/* 空状态提示 */}
                {messages.length === 0 && !isLoading && (
                    <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                        描述你想要的页面，Agent 将为你生成
                    </div>
                )}

                {/* 消息列表 */}
                {messages.map((msg) => (
                    <MessageBubble key={msg.id} message={msg} />
                ))}

                {/* 思考过程展示 */}
                <ThinkingPanel
                    thinkingSteps={thinkingSteps}
                    currentToolCall={currentToolCall}
                    isLoading={isLoading}
                />

                {/* 滚动锚点 */}
                <div ref={messagesEndRef} />

                {/* 回到底部浮动按钮（用户上滑时显示） */}
                {!isAtBottom && (
                    <button
                        onClick={() => {
                            messagesEndRef.current?.scrollIntoView({
                                behavior: "smooth",
                            });
                        }}
                        className="sticky bottom-4 left-1/2 -translate-x-1/2 z-10
                            flex items-center justify-center w-8 h-8 rounded-full
                            bg-white border border-gray-300 shadow-md
                            text-gray-500 hover:text-gray-700 hover:bg-gray-50
                            transition-colors"
                        title="回到底部"
                    >
                        <ChevronDown size={16} />
                    </button>
                )}
            </div>

            {/* 输入区域 */}
            <div className="border-t border-gray-200 px-4 py-3">
                <div className="flex items-end gap-2">
                    {/* 多行文本输入框 */}
                    <textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        onCompositionStart={() => setIsComposing(true)}
                        onCompositionEnd={() => setIsComposing(false)}
                        placeholder="描述你想要的页面..."
                        rows={1}
                        className="flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm
                            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                            disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled={isLoading}
                    />

                    {/* 发送 / 停止按钮 */}
                    {isLoading ? (
                        <button
                            onClick={onStopGeneration}
                            className="flex items-center justify-center w-9 h-9 rounded-lg
                                bg-red-500 text-white hover:bg-red-600 transition-colors"
                            title="停止生成"
                        >
                            <Square size={16} />
                        </button>
                    ) : (
                        <button
                            onClick={handleSubmit}
                            disabled={!input.trim()}
                            className="flex items-center justify-center w-9 h-9 rounded-lg
                                bg-blue-600 text-white hover:bg-blue-700 transition-colors
                                disabled:opacity-50 disabled:cursor-not-allowed"
                            title="发送"
                        >
                            <Send size={16} />
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}