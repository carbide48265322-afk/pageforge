import { useState, useEffect } from "react";
import { Eye } from "lucide-react";
import { useSession } from "./hooks/useSession";
import { useSSE } from "./hooks/useSSE";
import { ChatPanel } from "./components/ChatPanel";
import { PreviewPanel } from "./components/PreviewPanel";
import { ResizableLayout } from "./components/ResizableLayout";
import { VersionSelector } from "./components/VersionSelector";
import { BaseConfirmDialog } from "./components/BaseConfirmDialog";
import type { PageVersion } from "./services/api";

/**
 * PageForge 主应用
 * 组合聊天面板、预览面板、版本管理等核心功能
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

  // SSE 流式通信
  const {
    messages,
    isLoading,
    thinkingSteps,
    currentToolCall,
    latestHtml,
    sendMessage,
    stopGeneration,
  } = useSSE(sessionId);

  // 预览面板状态
  const [previewOpen, setPreviewOpen] = useState(false);

  // 基准版本切换确认弹窗状态
  const [pendingVersion, setPendingVersion] = useState<PageVersion | null>(null);
  // 新增：预览区显示的 HTML（SSE 推送或版本加载）
  const [previewHtml, setPreviewHtml] = useState("")
  // 应用启动时自动创建会话
  useEffect(() => {
    newSession();
  }, []);

  // SSE 完成后刷新版本列表
  useEffect(() => {
    if (!isLoading && sessionId && messages.length > 0) {
      loadVersions();
    }
  }, [isLoading]);

  // useSSE 的 latestHtml 变化时同步到 previewHtml
  useEffect(() => {
    if (latestHtml) {
      setPreviewHtml(latestHtml);
    }
  }, [latestHtml]);

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
    setPreviewHtml(res.html);  // ← 用加载的 HTML 更新预览
    setPreviewOpen(true);
    setPendingVersion(null);
  };

  return (
    <div className="h-screen flex flex-col bg-white">
      {/* 顶部导航栏 */}
      <header className="flex items-center justify-between border-b border-gray-200 px-4 py-2 shrink-0">
        <div className="flex items-center gap-3">
          <h1 className="text-base font-semibold text-gray-900">PageForge</h1>
          <span className="text-xs text-gray-400">AI 页面生成器</span>
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
            className={`flex items-center gap-1.5 px-2 py-1 text-xs rounded transition-colors ${previewOpen
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
            <ChatPanel
              messages={messages}
              isLoading={isLoading}
              thinkingSteps={thinkingSteps}
              currentToolCall={currentToolCall}
              onSendMessage={sendMessage}
              onStopGeneration={stopGeneration}
            />
          }
          rightPanel={
            <PreviewPanel
              html={previewHtml}
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