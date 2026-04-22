import React, { useState, useRef, useEffect } from "react";
import { Send, Square, ChevronDown, Wrench, Check, Loader2 } from "lucide-react";

import type { Message } from "../services/api";
import type { RenderBlock } from "../hooks/useSSE";
import { MessageBubble } from "./MessageBubble";
import { GenerationCard } from "./GenerationCard";
/** ChatPanel 组件的 props */
interface ChatPanelProps {
    messages: Message[];
    isLoading: boolean;
    currentBlocks: RenderBlock[];
    completedTurns: { userMsg: Message; blocks: RenderBlock[] }[];
    latestVersion: number;
    onSendMessage: (content: string) => void;
    onStopGeneration: () => void;
    onPreview: () => void;
}
/**
 * 聊天面板组件
 * 包含消息列表、思考过程展示、输入框和操作按钮
 * 使用 IntersectionObserver 实现智能滚动
 */
function ChatPanelComponent({
    messages,
    isLoading,
    currentBlocks,
    completedTurns,
    latestVersion,
    onSendMessage,
    onStopGeneration,
    onPreview,
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

    // 智能滚动：加载中始终跟随底部，加载完后仅在底部时跟随
    useEffect(() => {
        if (isLoading) {
            messagesEndRef.current?.scrollIntoView({ behavior: "instant" });
        } else if (isAtBottom) {
            messagesEndRef.current?.scrollIntoView({ behavior: "instant" });
        }
    }, [messages, currentBlocks, isLoading, isAtBottom]);


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


    /** 渲染 blocks 列表：Think → Tool → Content */
    const renderBlocks = (blocks: RenderBlock[]) => {
        const reasonings = blocks.filter((b) => b.type === "reasoning");
        const tools = blocks.filter((b) => b.type === "tool_call");
        const contents = blocks.filter((b) => b.type === "text" || b.type === "generation");

        return (
            <>
                {reasonings.length > 0 && (
                    <div className="mb-2">
                        <div className="flex items-center gap-2 text-xs text-gray-400 mb-1">
                            <Loader2 size={12} className={reasonings.some((r) => r.status === "streaming") ? "animate-spin" : ""} />
                            <span>Agent 思考中</span>
                        </div>
                        <div className="bg-gray-50 rounded-lg px-3 py-2 text-xs text-gray-600 whitespace-pre-wrap">
                            {reasonings.map((r) => r.content).join("")}
                        </div>
                    </div>
                )}
                {tools.map((block) => (
                    <div key={block.id} className="mb-2 flex items-center gap-2 text-xs text-gray-500 px-1">
                        <Wrench size={12} />
                        <span>{block.tool}</span>
                        {block.status === "done" ? (
                            <Check size={12} className="text-green-500" />
                        ) : (
                            <Loader2 size={12} className="animate-spin text-blue-500" />
                        )}
                    </div>
                ))}
                {contents.map((block) => {
                    if (block.type === "generation") {
                        return (
                            <GenerationCard
                                key={block.id}
                                isLoading={block.status === "loading"}
                                version={latestVersion}
                                requirement={messages.find((m) => m.role === "user")?.content || ""}
                                onPreview={onPreview}
                            />
                        );
                    }
                    return (
                        <MessageBubble
                            key={block.id}
                            message={{
                                id: block.id,
                                session_id: "",
                                role: "assistant",
                                content: block.content,
                                timestamp: new Date().toISOString(),
                                tool_calls: [],
                                html_version: null,
                            }}
                        />
                    );
                })}
            </>
        );
    };

    return (
        <div className="flex flex-col h-full">
            {/* 消息列表区域 */}
            <div
                ref={scrollContainerRef}
                className="flex-1 overflow-y-auto px-4 py-4"
            >
                {/* 空状态提示 */}
                {completedTurns.length === 0 && currentBlocks.length === 0 && !isLoading && (
                    <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                        描述你想要的页面，Agent 将为你生成
                    </div>
                )}
                {/* 历史轮次 */}
                {completedTurns.map((turn) => (
                    <div key={turn.userMsg.id}>
                        <MessageBubble message={turn.userMsg} />
                        {turn.blocks.length > 0 && renderBlocks(turn.blocks)}
                    </div>
                ))}
                {/* 当前轮次用户消息 */}
                {isLoading && messages.length > 0 && (
                    <MessageBubble message={messages[messages.length - 1]} />
                )}
                {/* 当前流式渲染块 */}
                {currentBlocks.length > 0 && renderBlocks(currentBlocks)}
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

export const ChatPanel = React.memo(ChatPanelComponent);