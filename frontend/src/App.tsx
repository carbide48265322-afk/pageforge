import { useState, useEffect, useRef } from "react";
import { Eye, Rocket } from "lucide-react";
import { useSession } from "./hooks/useSession";
import { useSSEv2, type PreviewSource } from "./hooks/useSSEv2";
import { useWebContainer } from "./hooks/useWebContainer";
import { ChatPanelV2 } from "./components/ChatPanelV2";
import { PreviewPanel } from "./components/PreviewPanel";
import { ResizableLayout } from "./components/ResizableLayout";
import { VersionSelector } from "./components/VersionSelector";
import { BaseConfirmDialog } from "./components/BaseConfirmDialog";
import type { PageVersion } from "./services/api";
import type { FileNode } from "./components/FileTree";

/**
 * PageForge 主应用（v2）
 * 支持多文件项目生成和预览
 *
 * 数据流（按改造计划第5.5节三阶段模型）：
 *
 * 1. 用户发送消息 → 后端 SSE 推送事件
 * 2. status:init → 前端 startContainer() → WebContainer.boot() + pnpm install 并行
 * 3. file_created/file_updated → 前端 writeFile() 写入 WebContainer FS（与安装并行）
 * 4. status:generation_done → 前端 startDevServer() → pnpm run dev → 拿到 URL
 * 5. URL 设给 previewSource（url 模式）→ PreviewPanel iframe 展示预览
 */
function App() {
  // 会话管理
  const {
    sessionId,
    versions,
    currentBase,
    newSession,
    loadVersions,
    switchBaseVersion,
    loadHtml,
  } = useSession();

  // SSE 流式通信（使用 v2 版本）
  const {
    messages,
    isLoading,
    currentBlocks,
    completedTurns,
    previewSource,
    files,
    latestVersion,
    intentResult,
    generationDone,       // 新增：文件生成完成标志
    setPreviewSource,     // 新增：手动设置预览源（供 WebContainer 用）
    sendMessage,
    stopGeneration,
    clearMessages,
  } = useSSEv2(sessionId);

  // WebContainer 三阶段管理
  const webContainer = useWebContainer(sessionId);

  // 预览面板状态
  const [previewOpen, setPreviewOpen] = useState(false);

  // 当前选中的文件
  const [selectedFile, setSelectedFile] = useState<string>("");

  // 是否已触发过 WebContainer 启动（防止重复触发）
  const wcStartedRef = useRef(false);

  // 基准版本切换确认弹窗状态
  const [pendingVersion, setPendingVersion] = useState<PageVersion | null>(null);

  // 应用启动时自动创建会话
  useEffect(() => {
    newSession();
  }, []);

  // 有预览内容时自动打开预览面板
  useEffect(() => {
    if (previewSource.mode !== 'none' && !previewOpen) {
      setPreviewOpen(true);
    }
  }, [previewSource]);

  // SSE 完成后刷新版本列表
  useEffect(() => {
    if (!isLoading && sessionId && messages.length > 0) {
      loadVersions();
    }
  }, [isLoading]);

  /**
   * 核心：连接 SSE 状态机 → WebContainer 三阶段启动
   *
   * 监听 useSSEv2 的状态变化，驱动 WebContainer 各阶段：
   * - status:init → 触发 startContainer（阶段1）
   * - file_created/file_updated → 触发 writeFile（阶段2，并行写入）
   * - status:generation_done → 触发 startDevServer（阶段3）
   */
  useEffect(() => {
    if (!sessionId || isLoading) return;

    // 获取最后一个 status 类型的 block
    const lastStatusBlock = [...currentBlocks].reverse().find(b => b.type === "status");
    if (!lastStatusBlock?.status_info?.status) return;

    const status = lastStatusBlock.status_info.status as string;
    const phase = webContainer.phase;

    switch (status) {
      case "init":
        // 阶段1：初始化 + pnpm install
        if (phase === "idle") {
          console.log("[App] 收到 status:init → 启动 WebContainer（阶段1）");
          webContainer.startContainer();
          wcStartedRef.current = true; // 标记已启动
        }
        break;

      case "generation_done":
        // 阶段3：启动 dev server
        if (wcStartedRef.current &&
            (phase === "waiting_files" || phase === "installing" || phase === "idle")) {
          console.log("[App] 收到 status:generation_done → 启动开发服务器（阶段3）");
          webContainer.startDevServer().then(() => {
            // startDevServer 内部会设置 previewUrl，这里等它设置完再更新 previewSource
            // 通过监听 webContainer.previewUrl 变化来更新 previewSource（见下方 effect）
          });
        }
        break;

      default:
        break;
    }
  }, [currentBlocks, sessionId, isLoading]); // eslint-disable-line react-hooks/exhaustive-deps

  /**
   * 文件生成事件 → 写入 WebContainer FS（阶段2）
   *
   * 当收到 file_created 或 file_updated 时，从后端获取文件内容并写入 WebContainer
   * 注意：这个 effect 只在 files 列表变化时触发
   */
  useEffect(() => {
    // 只有 WebContainer 已启动且处于 waiting_files/installing 阶段才写入
    if (!sessionId ||
        (webContainer.phase !== "waiting_files" && webContainer.phase !== "installing")) {
      return;
    }

    // 获取最新创建的文件
    const latestFiles = files.filter(f =>
      f.path // 有 path 的 FileInfo 才是有效的
    );

    if (latestFiles.length === 0) return;

    // 异步写入每个新文件（不阻塞 UI）
    for (const fileInfo of latestFiles) {
      // 从后端 API 获取文件内容并写入 WebContainer
      fetch(`http://localhost:9565/api/projects/${sessionId}/content?path=${encodeURIComponent(fileInfo.path)}`)
        .then(res => res.json())
        .then(data => {
          if (data.content) {
            webContainer.writeFile(fileInfo.path, data.content);
          }
        })
        .catch(err => {
          console.warn(`[App] 获取文件 ${fileInfo.path} 内容失败:`, err);
        });
    }
  }, [files, sessionId, webContainer.phase]); // eslint-disable-line react-hooks/exhaustive-deps

  /**
   * WebContainer dev server 就绪 → 更新 previewSource
   *
   * 当 WebContainer 的 previewUrl 变化时，自动将 previewSource 切换为 url 模式
   * 这是整个数据流的关键收口点
   */
  useEffect(() => {
    if (webContainer.previewUrl) {
      console.log(`[App] WebContainer dev server 就绪: ${webContainer.previewUrl}`);
      setPreviewSource({ mode: 'url', url: webContainer.previewUrl });
      setPreviewOpen(true);
    }
  }, [webContainer.previewUrl]); // eslint-disable-line react-hooks/exhaustive-deps

  /** 选择版本 → 弹出确认 */
  const handleSelectVersion = (version: PageVersion) => {
    setPendingVersion(version);
  };

  /** 确认切换基准版本 */
  const handleConfirmSwitch = async () => {
    if (!pendingVersion) return;
    await switchBaseVersion(pendingVersion.version);
    // 加载目标版本的 HTML 到预览
    const res = await loadHtml(pendingVersion.version);
    if (res.type === "html") {
      setPreviewSource({ mode: 'html', html: res.html });
    }
    setPreviewOpen(true);
    setPendingVersion(null);
  };

  /** 文件选择处理 */
  const handleFileSelect = (path: string) => {
    setSelectedFile(path);
    // TODO: 从后端加载文件内容
  };

  return (
    <div className="h-screen flex flex-col bg-white">

      {/* 顶部导航栏 */}
      <header className="flex items-center justify-between border-b border-gray-200 px-4 py-2 shrink-0">
        <div className="flex items-center gap-3">
          <h1 className="text-base font-semibold text-gray-900">PageForge</h1>
          <span className="text-xs text-gray-400">AI 项目生成器 (v2)</span>
          {/* WebContainer 状态指示器 */}
          {webContainer.phase !== "idle" && (
            <span className={`text-xs px-2 py-0.5 rounded-full ${
              webContainer.phase === "ready"
                ? "bg-green-100 text-green-700"
                : webContainer.phase === "error"
                  ? "bg-red-100 text-red-700"
                  : "bg-blue-100 text-blue-700 animate-pulse"
            }`}>
              {webContainer.statusMessage}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {/* 版本选择器 */}
          <VersionSelector
            versions={versions}
            currentBase={currentBase}
            onSelectVersion={handleSelectVersion}
          />

          {/* 预览按钮 */}
          <button
            onClick={() => setPreviewOpen(!previewOpen)}
            className={`flex items-center gap-1.5 px-2 py-1 text-xs rounded transition-colors ${
              previewOpen
                ? "bg-blue-100 text-blue-700"
                : "border border-gray-200 text-gray-600 hover:bg-gray-50"
            }`}
          >
            <Eye size={12} />
            预览
          </button>
        </div>
      </header>

      {/* 主内容区：可拖拽分栏 */}
      <main className="flex-1 overflow-hidden">
        <ResizableLayout
          leftPanel={
            <ChatPanelV2
              messages={messages}
              isLoading={isLoading}
              currentBlocks={currentBlocks}
              completedTurns={completedTurns}
              latestVersion={latestVersion}
              onSendMessage={sendMessage}
              onStopGeneration={stopGeneration}
              onPreview={() => setPreviewOpen(true)}
            />
          }
          rightPanel={
            <PreviewPanel
              previewSource={previewSource}
              files={files as any}
              selectedFile={selectedFile}
              onFileSelect={handleFileSelect}
              isOpen={previewOpen}
              onClose={() => setPreviewOpen(false)}
            />
          }
          isRightOpen={previewOpen}
        />
      </main>

      {/* 基准版本切换确认弹窗 */}
      {pendingVersion && (
        <BaseConfirmDialog
          targetVersion={pendingVersion}
          currentBase={currentBase}
          onConfirm={handleConfirmSwitch}
          onCancel={() => setPendingVersion(null)}
        />
      )}
    </div>
  );
}

export default App;
