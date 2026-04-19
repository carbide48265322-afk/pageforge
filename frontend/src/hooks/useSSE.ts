import { useState, useCallback, useRef } from "react";
import { sendMessageSSE, type Message, type ToolCall } from "../services/api";

/** Agent 思考步骤的类型 */
export interface ThinkingStep {
    /** 步骤序号 */
    index: number;
    /** 思考内容 */
    content: string;
    /** 时间戳 */
    timestamp: number;
}

/** useSSE hook 返回的状态和方法 */
export interface UseSSEReturn {
    /** 消息列表 */
    messages: Message[];
    /** 是否正在流式响应中 */
    isLoading: boolean;
    /** 当前 Agent 的思考步骤 */
    thinkingSteps: ThinkingStep[];
    /** 当前正在执行的工具调用 */
    currentToolCall: ToolCall | null;
    /** 最新的 HTML 内容（用于实时更新预览） */
    latestHtml: string;
    /** 发送消息给 Agent */
    sendMessage: (content: string) => void;
    /** 停止当前生成 */
    stopGeneration: () => void;
    /** 清空对话 */
    clearMessages: () => void;
}

/**
 * SSE 流式通信 Hook
 * 封装与后端 Agent 的流式交互，管理消息状态、思考步骤、工具调用等
 */
export function useSSE(sessionId: string | null): UseSSEReturn {
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([]);
    const [currentToolCall, setCurrentToolCall] = useState<ToolCall | null>(
        null,
    );
    const [latestHtml, setLatestHtml] = useState("");

    // 持有 AbortController，用于取消正在进行的 SSE 请求
    const abortRef = useRef<AbortController | null>(null);

    /** 发送消息并处理 SSE 流式响应 */
    const sendMessage = useCallback(
        (content: string) => {
            if (!sessionId || isLoading) return;

            // 添加用户消息到列表
            const userMessage: Message = {
                id: `local-${Date.now()}`,
                session_id: sessionId,
                role: "user",
                content,
                timestamp: new Date().toISOString(),
                tool_calls: [],
                html_version: null,
            };
            setMessages((prev) => [...prev, userMessage]);
            setIsLoading(true);
            setThinkingSteps([]);
            setCurrentToolCall(null);

            // 累积 assistant 回复内容
            let assistantContent = "";
            // 思考步骤计数器
            let stepIndex = 0;

            // 发起 SSE 请求，保存 AbortController 用于后续取消
            abortRef.current = sendMessageSSE(sessionId, content, {
                // Agent 开始思考
                onThinking: (content: string) => {
                    stepIndex++;
                    setThinkingSteps((prev) => [
                        ...prev,
                        {
                            index: stepIndex,
                            content,
                            timestamp: Date.now(),
                        },
                    ]);
                },

                // Agent 调用工具
                onToolCall: (tool: string, args: Record<string, unknown>) => {
                    setCurrentToolCall({ tool, args });
                },

                // 工具返回结果
                onToolResult: (_tool: string, _result: unknown) => {
                    setCurrentToolCall(null);
                },

                // HTML 内容更新（实时推送到预览）
                onHtmlUpdate: (html: string, _version: number) => {
                    setLatestHtml(html);
                },

                // Agent 文本回复（流式累积，实现打字机效果）
                onMessage: (content: string) => {
                    assistantContent += content;
                    setMessages((prev) => {
                        const newMessages = [...prev];
                        const lastMsg = newMessages[newMessages.length - 1];
                        if (lastMsg && lastMsg.role === "assistant") {
                            // 追加到已有的 assistant 消息
                            newMessages[newMessages.length - 1] = {
                                ...lastMsg,
                                content: assistantContent,
                            };
                        } else {
                            // 创建新的 assistant 消息
                            newMessages.push({
                                id: `local-${Date.now()}`,
                                session_id: sessionId,
                                role: "assistant",
                                content: assistantContent,
                                timestamp: new Date().toISOString(),
                                tool_calls: [],
                                html_version: null,
                            });
                        }
                        return newMessages;
                    });
                },

                // 流式响应结束
                onDone: (_version: number) => {
                    setIsLoading(false);
                    setCurrentToolCall(null);
                    abortRef.current = null;
                },

                // 错误处理
                onError: (errorMsg: string) => {
                    console.error("SSE 错误:", errorMsg);
                    setMessages((prev) => [
                        ...prev,
                        {
                            id: `local-${Date.now()}`,
                            session_id: sessionId,
                            role: "assistant",
                            content: `抱歉，出现错误：${errorMsg}`,
                            timestamp: new Date().toISOString(),
                            tool_calls: [],
                            html_version: null,
                        },
                    ]);
                    setIsLoading(false);
                    abortRef.current = null;
                },
            });
        },
        [sessionId, isLoading],
    );

    /** 停止当前生成 */
    const stopGeneration = useCallback(() => {
        abortRef.current?.abort();
        abortRef.current = null;
        setIsLoading(false);
        setCurrentToolCall(null);
    }, []);

    /** 清空对话历史 */
    const clearMessages = useCallback(() => {
        // 清空时也取消正在进行的请求
        abortRef.current?.abort();
        abortRef.current = null;
        setMessages([]);
        setThinkingSteps([]);
        setCurrentToolCall(null);
        setLatestHtml("");
    }, []);

    return {
        messages,
        isLoading,
        thinkingSteps,
        currentToolCall,
        latestHtml,
        sendMessage,
        stopGeneration,
        clearMessages,
    };
}
