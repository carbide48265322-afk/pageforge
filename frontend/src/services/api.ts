const API_BASE = "http://localhost:8000/api";

// ==================== 类型定义 ====================

/** 会话数据 */
export interface Session {
    id: string;
    created_at: string;
    updated_at: string;
    messages: Message[];
    current_base_version: number;
}

/** 消息数据 */
export interface Message {
    id: string;
    session_id: string;
    role: "user" | "assistant";
    content: string;
    timestamp: string;
    tool_calls: ToolCall[];
    html_version: number | null;
}

/** 工具调用记录 */
export interface ToolCall {
    tool: string;
    args: Record<string, unknown>;
    result?: unknown;
}

/** 页面版本元数据 */
export interface PageVersion {
    version: number;
    session_id: string;
    timestamp: string;
    summary: string;
    parent_version: number | null;
    trigger_message: string;
}

/** 版本列表响应 */
export interface VersionsResponse {
    versions: PageVersion[];
    current_base: number;
}

// ==================== API 函数 ====================

/** 创建新会话 */
export async function createSession(): Promise<{ session_id: string }> {
    const res = await fetch(`${API_BASE}/sessions`, { method: "POST" });
    return res.json();
}

/** 获取版本列表 */
export async function getVersions(
    sessionId: string,
): Promise<VersionsResponse> {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}/versions`);
    return res.json();
}

/** 获取指定版本的 HTML */
export async function getHtml(
    sessionId: string,
    version?: number,
): Promise<{ html: string; version: number }> {
    const params = version ? `?version=${version}` : "";
    const res = await fetch(`${API_BASE}/sessions/${sessionId}/html${params}`);
    return res.json();
}

/** 切换基准版本 */
export async function setBaseVersion(
    sessionId: string,
    version: number,
): Promise<{ success: boolean; current_base: number }> {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}/base-version`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ version }),
    });
    return res.json();
}

/** 获取导出下载 URL */
export function getExportUrl(sessionId: string, version?: number): string {
    const params = version ? `?version=${version}` : "";
    return `${API_BASE}/sessions/${sessionId}/export${params}`;
}

// ==================== SSE 消息发送 ====================

/** SSE 事件回调接口 */
interface SSEHandlers {
    onMessageStart?: () => void;
    onReasoningChunk?: (blockId: string, content: string) => void;
    onToolCall?: (
        blockId: string,
        tool: string,
        args: Record<string, unknown>,
    ) => void;
    onToolResult?: (blockId: string, tool: string, result: unknown) => void;
    onGenerationStart?: (blockId: string) => void;
    onGenerationDone?: (blockId: string) => void;
    onChunkDelta?: (content: string) => void;
    onHtmlStream?: (content: string) => void;
    onHtmlUpdate?: (html: string, version: number) => void;
    onDone?: () => void;
    onError?: (content: string) => void;
}

/**
 * 发送消息并通过 SSE 流式接收事件
 * 返回 AbortController 用于取消请求
 */
export function sendMessageSSE(
    sessionId: string,
    message: string,
    handlers: SSEHandlers,
): AbortController {
    const controller = new AbortController();

    fetch(`${API_BASE}/sessions/${sessionId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
        signal: controller.signal,
    })
        .then(async (res) => {
            if (!res.ok || !res.body) throw new Error("Stream failed");

            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            // 逐块读取 SSE 流
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";

                let currentEvent = "";
                for (const line of lines) {
                    if (line.startsWith("event: ")) {
                        currentEvent = line.slice(7).trim();
                    } else if (line.startsWith("data: ")) {
                        const dataStr = line.slice(6);
                        try {
                            const data = JSON.parse(dataStr);
                            // 根据事件类型分发到对应回调
                            switch (currentEvent) {
                                case "MESSAGE_START":
                                    handlers.onMessageStart?.();
                                    break;
                                case "REASONING_CHUNK":
                                    handlers.onReasoningChunk?.(
                                        data.block_id,
                                        data.content,
                                    );
                                    break;
                                case "TOOL_CALL":
                                    handlers.onToolCall?.(
                                        data.block_id,
                                        data.tool,
                                        data.args,
                                    );
                                    break;
                                case "TOOL_RESULT":
                                    handlers.onToolResult?.(
                                        data.block_id,
                                        data.tool,
                                        data.result,
                                    );
                                    break;
                                case "GENERATION_START":
                                    handlers.onGenerationStart?.(data.block_id);
                                    break;
                                case "GENERATION_DONE":
                                    handlers.onGenerationDone?.(data.block_id);
                                    break;
                                case "HTML_STREAM":
                                    handlers.onHtmlStream?.(data.content);
                                    break;
                                case "CHUNK_DELTA":
                                    handlers.onChunkDelta?.(data.content);
                                    break;
                                case "HTML_UPDATE":
                                    handlers.onHtmlUpdate?.(
                                        data.html,
                                        data.version,
                                    );
                                    break;
                                case "done":
                                    handlers.onDone?.();
                                    break;
                                case "error":
                                    handlers.onError?.(data.content);
                                    break;
                            }
                        } catch {
                            // 忽略 JSON 解析错误
                        }
                        currentEvent = "";
                    }
                }
            }
        })
        .catch((err) => {
            if (err.name !== "AbortError") {
                handlers.onError?.(err.message);
            }
        });

    return controller;
}
