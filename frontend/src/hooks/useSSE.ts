import { useState, useCallback, useRef, useEffect } from "react";
import { sendMessageSSE, type Message, type HumanInputRequest } from "../services/api";

/** 渲染块类型 */
export type BlockType = "reasoning" | "text" | "tool_call" | "generation";

/** 渲染块 */
export interface RenderBlock {
    /** 块唯一 ID */
    id: string;
    /** 块类型 */
    type: BlockType;
    /** 块内容（reasoning/text 增量追加） */
    content: string;
    /** 块状态 */
    status: "streaming" | "done" | "loading";
    /** tool_call 特有：工具名 */
    tool?: string;
    /** tool_call 特有：工具参数 */
    args?: Record<string, unknown>;
    /** tool_call 特有：工具返回结果 */
    result?: unknown;
    /** generation 特有：版本号 */
    version?: number;
}

/** useSSE hook 返回值 */
export interface UseSSEReturn {
    /** 消息列表（已完成的消息） */
    messages: Message[];
    /** 当前流式响应的渲染块列表 */
    currentBlocks: RenderBlock[];
    /** 已完成的对话轮次（包含用户消息和 AI 渲染块） */
    completedTurns: { userMsg: Message; blocks: RenderBlock[] }[];
    /** 是否正在流式响应中 */
    isLoading: boolean;
    /** 最新的 HTML 内容（预览 iframe 用） */
    latestHtml: string;
    /** 流式输出的 HTML（预览面板源码视图实时展示） */
    streamingHtml: string;
    /** 最新生成的版本号 */
    latestVersion: number;
    /** 人机协作请求 */
    humanInputRequest: HumanInputRequest | null;
    /** 发送消息 */
    sendMessage: (content: string) => void;
    /** 提交人机协作响应 */
    submitHumanInput: (data: { action: string; [key: string]: any }) => void;
    /** 停止生成 */
    stopGeneration: () => void;
    /** 清空对话 */
    clearMessages: () => void;
}

/**
 * SSE 流式通信 Hook
 * 基于扁平事件模型，将事件转换为有序的渲染块列表
 * 双背压缓冲：对话框（慢速打字效果）+ 源码视图（快速实时展示）
 */
export function useSSE(sessionId: string | null): UseSSEReturn {
    const [messages, setMessages] = useState<Message[]>([]);
    const [currentBlocks, setCurrentBlocks] = useState<RenderBlock[]>([]);
    const [completedTurns, setCompletedTurns] = useState<
        { userMsg: Message; blocks: RenderBlock[] }[]
    >([]);

    const [isLoading, setIsLoading] = useState(false);
    const [latestHtml, setLatestHtml] = useState("");
    const [streamingHtml, setStreamingHtml] = useState("");
    const [latestVersion, setLatestVersion] = useState(0);
    const [humanInputRequest, setHumanInputRequest] = useState<HumanInputRequest | null>(null);

    const abortRef = useRef<AbortController | null>(null);
    const blockIdRef = useRef(0);
    const blocksRef = useRef<RenderBlock[]>([]);

    // ---- 文本背压缓冲（对话框打字效果） ----
    const bufferRef = useRef<string[]>([]);
    const rafRef = useRef<number | null>(null);
    const consumerActiveRef = useRef(false);

    // ---- 源码视图背压缓冲（快速实时展示） ----
    const streamBufferRef = useRef<string[]>([]);
    const streamDisplayRef = useRef<string>("");
    const streamRafRef = useRef<number | null>(null);
    const streamActiveRef = useRef(false);

    const messagesRef = useRef<Message[]>([]);

    /** 生成块 ID */
    const nextBlockId = useCallback(() => {
        blockIdRef.current += 1;
        return `blk_${blockIdRef.current}`;
    }, []);

    /** 文本消费速率 */
    const getConsumeRate = useCallback(() => {
        const len = bufferRef.current.length;
        if (len > 50) return 8;
        if (len > 20) return 4;
        if (len > 5) return 2;
        return 1;
    }, []);

    /** 文本消费：追加到最后一个 text block */
    const flushBuffer = useCallback(() => {
        const rate = getConsumeRate();
        const tokens = bufferRef.current.splice(0, rate);
        if (tokens.length === 0) return;
        const text = tokens.join("");
        const blocks = blocksRef.current;
        const last = blocks[blocks.length - 1];
        if (last && last.type === "text" && last.status === "streaming") {
            last.content += text;
        }
        setCurrentBlocks([...blocks]);
    }, [getConsumeRate]);

    /** 启动文本消费循环 */
    const startConsumer = useCallback(() => {
        if (consumerActiveRef.current) return;
        consumerActiveRef.current = true;
        const loop = () => {
            if (!consumerActiveRef.current) return;
            flushBuffer();
            rafRef.current = requestAnimationFrame(loop);
        };
        rafRef.current = requestAnimationFrame(loop);
    }, [flushBuffer]);

    /** 停止文本消费循环 */
    const stopConsumer = useCallback(() => {
        consumerActiveRef.current = false;
        if (rafRef.current !== null) {
            cancelAnimationFrame(rafRef.current);
            rafRef.current = null;
        }
        if (bufferRef.current.length > 0) {
            const text = bufferRef.current.join("");
            bufferRef.current = [];
            const blocks = blocksRef.current;
            const last = blocks[blocks.length - 1];
            if (last && last.type === "text" && last.status === "streaming") {
                last.content += text;
            }
            setCurrentBlocks([...blocks]);
        }
    }, []);

    /** 源码消费速率（比对话框快） */
    const getStreamRate = useCallback(() => {
        const len = streamBufferRef.current.length;
        if (len > 100) return 20;
        if (len > 50) return 10;
        if (len > 20) return 5;
        return 3;
    }, []);

    /** 源码消费 */
    const flushStreamBuffer = useCallback(() => {
        const rate = getStreamRate();
        const tokens = streamBufferRef.current.splice(0, rate);
        if (tokens.length === 0) return;
        streamDisplayRef.current += tokens.join("");
        setStreamingHtml(streamDisplayRef.current);
    }, [getStreamRate]);

    /** 启动源码消费循环 */
    const startStreamConsumer = useCallback(() => {
        if (streamActiveRef.current) return;
        streamActiveRef.current = true;
        const loop = () => {
            if (!streamActiveRef.current) return;
            flushStreamBuffer();
            streamRafRef.current = requestAnimationFrame(loop);
        };
        streamRafRef.current = requestAnimationFrame(loop);
    }, [flushStreamBuffer]);

    /** 停止源码消费循环 */
    const stopStreamConsumer = useCallback(() => {
        streamActiveRef.current = false;
        if (streamRafRef.current !== null) {
            cancelAnimationFrame(streamRafRef.current);
            streamRafRef.current = null;
        }
        if (streamBufferRef.current.length > 0) {
            streamDisplayRef.current += streamBufferRef.current.join("");
            streamBufferRef.current = [];
            setStreamingHtml(streamDisplayRef.current);
        }
    }, []);

    // 组件卸载时清理
    useEffect(() => {
        return () => {
            stopConsumer();
            stopStreamConsumer();
        };
    }, [stopConsumer, stopStreamConsumer]);

    /** 发送消息并处理 SSE 流式响应 */
    const sendMessage = useCallback(
        (content: string) => {
            if (!sessionId || isLoading) return;

            // 添加用户消息
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
            messagesRef.current = [...messagesRef.current, userMessage];

            setIsLoading(true);
            setCurrentBlocks([]);
            blocksRef.current = [];
            bufferRef.current = [];
            streamBufferRef.current = [];
            streamDisplayRef.current = "";
            blockIdRef.current = 0;

            startConsumer();
            startStreamConsumer();

            abortRef.current = sendMessageSSE(sessionId, content, {
                onMessageStart: () => {},

                // 思考增量 — 用后端 block_id 查找或新建
                onReasoningChunk: (blockId: string, chunk: string) => {
                    const blocks = blocksRef.current;
                    const existing = blocks.find((b) => b.id === blockId);
                    if (existing) {
                        existing.content += "\n" + chunk;
                    } else {
                        blocks.push({
                            id: blockId,
                            type: "reasoning",
                            content: chunk,
                            status: "streaming",
                        });
                    }
                    setCurrentBlocks([...blocks]);
                },

                // 工具调用 — 用后端 block_id 新建 tool_call block
                onToolCall: (
                    blockId: string,
                    tool: string,
                    args: Record<string, unknown>,
                ) => {
                    blocksRef.current.push({
                        id: blockId,
                        type: "tool_call",
                        content: "",
                        status: "streaming",
                        tool,
                        args,
                    });
                    setCurrentBlocks([...blocksRef.current]);
                },

                // 工具结果 — 用后端 block_id 匹配更新
                onToolResult: (
                    blockId: string,
                    _tool: string,
                    result: unknown,
                ) => {
                    const blocks = blocksRef.current;
                    const target = blocks.find((b) => b.id === blockId);
                    if (target) {
                        target.result = result;
                        target.status = "done";
                    }
                    setCurrentBlocks([...blocks]);
                },

                // 生成开始 — 用后端 block_id 新建 generation block
                onGenerationStart: (blockId: string) => {
                    blocksRef.current.push({
                        id: blockId,
                        type: "generation",
                        content: "",
                        status: "loading",
                    });
                    setCurrentBlocks([...blocksRef.current]);
                },

                // 生成完成 — 用后端 block_id 匹配更新
                onGenerationDone: (blockId: string) => {
                    const blocks = blocksRef.current;
                    const target = blocks.find((b) => b.id === blockId);
                    if (target) {
                        target.status = "done";
                    }
                    setCurrentBlocks([...blocks]);
                },

                // 文本增量 — 推入背压缓冲
                onChunkDelta: (chunk: string) => {
                    const blocks = blocksRef.current;
                    const last = blocks[blocks.length - 1];
                    if (
                        last &&
                        last.type === "text" &&
                        last.status === "streaming"
                    ) {
                        bufferRef.current.push(chunk);
                    } else {
                        // 关闭之前的 reasoning block
                        if (
                            last &&
                            last.type === "reasoning" &&
                            last.status === "streaming"
                        ) {
                            last.status = "done";
                        }
                        blocks.push({
                            id: nextBlockId(),
                            type: "text",
                            content: "",
                            status: "streaming",
                        });
                        bufferRef.current.push(chunk);
                    }
                    setCurrentBlocks([...blocks]);
                },

                // HTML 源码流式推送 — 推入源码背压缓冲
                onHtmlStream: (content: string) => {
                    streamBufferRef.current.push(content);
                },

                // HTML 更新（预览 iframe）
                onHtmlUpdate: (html: string, version: number) => {
                    setLatestHtml(html);
                    setLatestVersion(version);
                },

                // 人机协作请求
                onHumanInputRequest: (request: HumanInputRequest) => {
                    setHumanInputRequest(request);
                    setIsLoading(false); // 暂停加载状态，等待用户输入
                    stopConsumer();
                    stopStreamConsumer();
                },

                // 流式结束
                onDone: () => {
                    stopConsumer();
                    stopStreamConsumer();
                    setIsLoading(false);
                    abortRef.current = null;
                    // 将所有块标记为 done
                    const blocks = blocksRef.current;
                    blocks.forEach((b) => {
                        if (b.status === "streaming" || b.status === "loading")
                            b.status = "done";
                    });
                    // 保存到历史轮次
                    const lastUserMsg =
                        messagesRef.current[messagesRef.current.length - 1];
                    if (
                        lastUserMsg &&
                        lastUserMsg.role === "user" &&
                        blocks.length > 0
                    ) {
                        setCompletedTurns((prev) => [
                            ...prev,
                            { userMsg: lastUserMsg, blocks: [...blocks] },
                        ]);
                    }
                    setCurrentBlocks([]);
                    blocksRef.current = [];
                },

                // 错误
                onError: (errorMsg: string) => {
                    stopConsumer();
                    stopStreamConsumer();
                    setIsLoading(false);
                    abortRef.current = null;
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
                    blocksRef.current = [];
                    setCurrentBlocks([]);
                },
            });
        },
        [
            sessionId,
            isLoading,
            startConsumer,
            stopConsumer,
            startStreamConsumer,
            stopStreamConsumer,
            nextBlockId,
        ],
    );

    /** 提交人机协作响应 */
    const submitHumanInput = useCallback((data: { action: string; [key: string]: any }) => {
        if (!sessionId || !humanInputRequest) return;
        
        // 发送响应并恢复执行
        const message = JSON.stringify(data);
        setHumanInputRequest(null);
        setIsLoading(true);
        
        // 重置状态
        setCurrentBlocks([]);
        blocksRef.current = [];
        bufferRef.current = [];
        streamBufferRef.current = [];
        streamDisplayRef.current = "";
        blockIdRef.current = 0;
        
        startConsumer();
        startStreamConsumer();
        
        abortRef.current = sendMessageSSE(sessionId, message, {
            onMessageStart: () => {},
            onReasoningChunk: (blockId: string, chunk: string) => {
                const blocks = blocksRef.current;
                const existing = blocks.find((b) => b.id === blockId);
                if (existing) {
                    existing.content += "\n" + chunk;
                } else {
                    blocks.push({
                        id: blockId,
                        type: "reasoning",
                        content: chunk,
                        status: "streaming",
                    });
                }
                setCurrentBlocks([...blocks]);
            },
            onToolCall: (blockId: string, tool: string, args: Record<string, unknown>) => {
                blocksRef.current.push({
                    id: blockId,
                    type: "tool_call",
                    content: "",
                    status: "streaming",
                    tool,
                    args,
                });
                setCurrentBlocks([...blocksRef.current]);
            },
            onToolResult: (blockId: string, _tool: string, result: unknown) => {
                const blocks = blocksRef.current;
                const target = blocks.find((b) => b.id === blockId);
                if (target) {
                    target.result = result;
                    target.status = "done";
                }
                setCurrentBlocks([...blocks]);
            },
            onGenerationStart: (blockId: string) => {
                blocksRef.current.push({
                    id: blockId,
                    type: "generation",
                    content: "",
                    status: "loading",
                });
                setCurrentBlocks([...blocksRef.current]);
            },
            onGenerationDone: (blockId: string) => {
                const blocks = blocksRef.current;
                const target = blocks.find((b) => b.id === blockId);
                if (target) {
                    target.status = "done";
                }
                setCurrentBlocks([...blocks]);
            },
            onChunkDelta: (chunk: string) => {
                const blocks = blocksRef.current;
                const last = blocks[blocks.length - 1];
                if (last && last.type === "text" && last.status === "streaming") {
                    bufferRef.current.push(chunk);
                } else {
                    if (last && last.type === "reasoning" && last.status === "streaming") {
                        last.status = "done";
                    }
                    blocks.push({
                        id: nextBlockId(),
                        type: "text",
                        content: "",
                        status: "streaming",
                    });
                    bufferRef.current.push(chunk);
                }
                setCurrentBlocks([...blocks]);
            },
            onHtmlStream: (content: string) => {
                streamBufferRef.current.push(content);
            },
            onHtmlUpdate: (html: string, version: number) => {
                setLatestHtml(html);
                setLatestVersion(version);
            },
            onHumanInputRequest: (request: HumanInputRequest) => {
                setHumanInputRequest(request);
                setIsLoading(false);
                stopConsumer();
                stopStreamConsumer();
            },
            onDone: () => {
                stopConsumer();
                stopStreamConsumer();
                setIsLoading(false);
                abortRef.current = null;
                const blocks = blocksRef.current;
                blocks.forEach((b) => {
                    if (b.status === "streaming" || b.status === "loading")
                        b.status = "done";
                });
                const lastUserMsg = messagesRef.current[messagesRef.current.length - 1];
                if (lastUserMsg && lastUserMsg.role === "user" && blocks.length > 0) {
                    setCompletedTurns((prev) => [
                        ...prev,
                        { userMsg: lastUserMsg, blocks: [...blocks] },
                    ]);
                }
                setCurrentBlocks([]);
                blocksRef.current = [];
            },
            onError: (errorMsg: string) => {
                stopConsumer();
                stopStreamConsumer();
                setIsLoading(false);
                abortRef.current = null;
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
                blocksRef.current = [];
                setCurrentBlocks([]);
            },
        });
    }, [sessionId, humanInputRequest, startConsumer, stopConsumer, startStreamConsumer, stopStreamConsumer, nextBlockId]);

    /** 停止当前生成 */
    const stopGeneration = useCallback(() => {
        abortRef.current?.abort();
        abortRef.current = null;
        stopConsumer();
        stopStreamConsumer();
        setIsLoading(false);
        blocksRef.current = [];
        setCurrentBlocks([]);
    }, [stopConsumer, stopStreamConsumer]);

    /** 清空对话 */
    const clearMessages = useCallback(() => {
        abortRef.current?.abort();
        abortRef.current = null;
        stopConsumer();
        stopStreamConsumer();
        setMessages([]);
        setCompletedTurns([]);
        messagesRef.current = [];
        setCurrentBlocks([]);
        blocksRef.current = [];
        setLatestHtml("");
        setStreamingHtml("");
        streamBufferRef.current = [];
        streamDisplayRef.current = "";
        setLatestVersion(0);
    }, [stopConsumer, stopStreamConsumer]);

    return {
        messages,
        currentBlocks,
        completedTurns,
        isLoading,
        latestHtml,
        streamingHtml,
        latestVersion,
        humanInputRequest,
        sendMessage,
        submitHumanInput,
        stopGeneration,
        clearMessages,
    };
}
