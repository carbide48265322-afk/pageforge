const API_BASE = "http://localhost:9565/api";

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

// ==================== WebContainer API ====================

/** WebContainer 项目信息 */
export interface WebContainerProject {
    project_path: string;
    files: string[];
    status: string;
}

/** WebContainer 项目状态 */
export interface WebContainerStatus {
    status: string;
    project_path?: string;
    existing_files: string[];
    missing_files: string[];
    has_node_modules: boolean;
    dependencies: Record<string, string>;
    dev_dependencies: Record<string, string>;
    message?: string;
}

/** WebContainer 依赖安装结果 */
export interface InstallResult {
    status: string;
    message: string;
    error?: string;
    stdout?: string;
}

/** WebContainer 服务器启动结果 */
export interface ServerResult {
    status: string;
    message: string;
    port?: number;
    url?: string;
    pid?: number;
    error?: string;
    stdout?: string;
}

/** WebContainer 文件信息 */
export interface ProjectFiles {
    project_path: string;
    files: Record<string, {
        content: string;
        size: number;
        modified: number;
        is_binary?: boolean;
    }>;
}

/** WebContainer 构建结果 */
export interface BuildResult {
    status: string;
    message: string;
    build_files?: string[];
    error?: string;
    stdout?: string;
}

/** 创建 WebContainer 项目 */
export async function createWebContainerProject(
    sessionId: string,
    version: number
): Promise<WebContainerProject> {
    const res = await fetch(`${API_BASE}/webcontainer/projects?session_id=${sessionId}&version=${version}`, {
        method: "POST"
    });
    if (!res.ok) {
        throw new Error(`创建项目失败: ${res.statusText}`);
    }
    return res.json();
}

/** 获取 WebContainer 项目状态 */
export async function getWebContainerStatus(
    sessionId: string,
    version: number
): Promise<WebContainerStatus> {
    const res = await fetch(`${API_BASE}/webcontainer/projects/${sessionId}/${version}/status`);
    if (!res.ok) {
        throw new Error(`获取项目状态失败: ${res.statusText}`);
    }
    return res.json();
}

/** 安装项目依赖 */
export async function installWebContainerDependencies(
    sessionId: string,
    version: number
): Promise<InstallResult> {
    const res = await fetch(`${API_BASE}/webcontainer/projects/${sessionId}/${version}/install`, {
        method: "POST"
    });
    if (!res.ok) {
        throw new Error(`安装依赖失败: ${res.statusText}`);
    }
    return res.json();
}

/** 启动开发服务器 */
export async function startWebContainerServer(
    sessionId: string,
    version: number
): Promise<ServerResult> {
    const res = await fetch(`${API_BASE}/webcontainer/projects/${sessionId}/${version}/start`, {
        method: "POST"
    });
    if (!res.ok) {
        throw new Error(`启动服务器失败: ${res.statusText}`);
    }
    return res.json();
}

/** 获取项目文件 */
export async function getWebContainerFiles(
    sessionId: string,
    version: number
): Promise<ProjectFiles> {
    const res = await fetch(`${API_BASE}/webcontainer/projects/${sessionId}/${version}/files`);
    if (!res.ok) {
        throw new Error(`获取文件失败: ${res.statusText}`);
    }
    return res.json();
}

/** 构建项目 */
export async function buildWebContainerProject(
    sessionId: string,
    version: number
): Promise<BuildResult> {
    const res = await fetch(`${API_BASE}/webcontainer/projects/${sessionId}/${version}/build`, {
        method: "POST"
    });
    if (!res.ok) {
        throw new Error(`构建项目失败: ${res.statusText}`);
    }
    return res.json();
}

/** 获取预览信息 */
export async function getWebContainerPreview(
    sessionId: string,
    version: number
): Promise<{
    session_id: string;
    version: number;
    status: string;
    project_ready: boolean;
    files_count: number;
}> {
    const res = await fetch(`${API_BASE}/webcontainer/projects/${sessionId}/${version}/preview`);
    if (!res.ok) {
        throw new Error(`获取预览信息失败: ${res.statusText}`);
    }
    return res.json();
}

/** 清理项目 */
export async function cleanupWebContainerProject(
    sessionId: string,
    version: number
): Promise<{ status: string; message: string; error?: string }> {
    const res = await fetch(`${API_BASE}/webcontainer/projects/${sessionId}/${version}`, {
        method: "DELETE"
    });
    if (!res.ok) {
        throw new Error(`清理项目失败: ${res.statusText}`);
    }
    return res.json();
}

/** 清理会话的所有项目 */
export async function cleanupWebContainerSession(
    sessionId: string
): Promise<{ status: string; message: string; error?: string }> {
    const res = await fetch(`${API_BASE}/webcontainer/projects/${sessionId}`, {
        method: "DELETE"
    });
    if (!res.ok) {
        throw new Error(`清理会话失败: ${res.statusText}`);
    }
    return res.json();
}

/** 从模板创建 React 项目 */
export async function createReactProjectFromTemplate(
    sessionId: string,
    version: number,
    templateName: string
): Promise<{ project_path: string; files: string[]; status: string; template: string }> {
    const res = await fetch(`${API_BASE}/webcontainer/projects/template`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            session_id: sessionId,
            version: version,
            template_name: templateName
        })
    });
    if (!res.ok) {
        throw new Error(`从模板创建项目失败: ${res.statusText}`);
    }
    return res.json();
}

/** 获取可用模板列表 */
export async function getAvailableTemplates(): Promise<Record<string, {
    name: string;
    description: string;
    features: string[];
}>> {
    const res = await fetch(`${API_BASE}/webcontainer/templates`);
    if (!res.ok) {
        throw new Error(`获取模板列表失败: ${res.statusText}`);
    }
    return res.json();
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
