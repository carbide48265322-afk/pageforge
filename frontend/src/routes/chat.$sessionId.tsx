import { createRoute, useParams, Link } from '@tanstack/react-router';
import { rootRoute } from './__root';
import { useState, useEffect, useRef } from 'react';
import { Eye, ArrowLeft, Rocket } from 'lucide-react';
import { useSession } from '../hooks/useSession';
import { useSSEv2 } from '../hooks/useSSEv2';
import { useWebContainer } from '../hooks/useWebContainer';
import { ChatPanelV2 } from '../components/ChatPanelV2';
import { PreviewPanel } from '../components/PreviewPanel';
import { ResizableLayout } from '../components/ResizableLayout';
import { VersionSelector } from '../components/VersionSelector';
import { BaseConfirmDialog } from '../components/BaseConfirmDialog';
import type { PageVersion } from '../services/api';
import '../services/mock/quick-fix';

export const chatRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/chat/$sessionId',
  component: ChatComponent,
});

function ChatComponent() {
  const params = useParams({ from: chatRoute.id });
  const sessionId = params.sessionId;

  const { versions, currentBase, loadVersions, switchBaseVersion, loadHtml, setSessionId: setSessionIdState } = useSession();

  useEffect(() => {
    if (sessionId) {
      setSessionIdState(sessionId);
    }
  }, [sessionId, setSessionIdState]);

  const { messages, isLoading, currentBlocks, completedTurns, previewSource, files, setPreviewSource, sendMessage, stopGeneration } = useSSEv2(sessionId);

  const webContainer = useWebContainer(sessionId);

  const [selectedFile, setSelectedFile] = useState<string>('');
  const wcStartedRef = useRef(false);
  const [pendingVersion, setPendingVersion] = useState<PageVersion | null>(null);

  useEffect(() => {
    if (!isLoading && sessionId && messages.length > 0) {
      loadVersions();
    }
  }, [isLoading]);

  useEffect(() => {
    if (!sessionId || isLoading) return;
    const lastStatusBlock = [...currentBlocks].reverse().find(b => b.type === "status");
    if (!lastStatusBlock?.status_info?.status) return;
    const status = lastStatusBlock.status_info.status as string;
    const phase = webContainer.phase;
    switch (status) {
      case "init":
        if (phase === "idle") {
          webContainer.startContainer();
          wcStartedRef.current = true;
        }
        break;
      case "generation_done":
        if (wcStartedRef.current && (phase === "waiting_files" || phase === "installing" || phase === "idle")) {
          webContainer.startDevServer();
        }
        break;
    }
  }, [currentBlocks, sessionId, isLoading]);

  useEffect(() => {
    if (!sessionId || (webContainer.phase !== "waiting_files" && webContainer.phase !== "installing")) {
      return;
    }
    const latestFiles = files.filter(f => f.path);
    if (latestFiles.length === 0) return;
    for (const fileInfo of latestFiles) {
      fetch(`http://localhost:9000/api/projects/${sessionId}/content?path=${encodeURIComponent(fileInfo.path)}`)
        .then(res => res.json())
        .then(data => {
          if (data.content) {
            webContainer.writeFile(fileInfo.path, data.content);
          }
        })
        .catch(err => {
          console.warn(`[Chat] 获取文件 ${fileInfo.path} 内容失败:`, err);
        });
    }
  }, [files, sessionId, webContainer.phase]);

  useEffect(() => {
    if (webContainer.previewUrl) {
      setPreviewSource({ mode: 'url', url: webContainer.previewUrl });
    }
  }, [webContainer.previewUrl]);

  const handleSelectVersion = (version: PageVersion) => {
    setPendingVersion(version);
  };

  const handleConfirmSwitch = async () => {
    if (!pendingVersion) return;
    await switchBaseVersion(pendingVersion.version);
    const res = await loadHtml(pendingVersion.version);
    if ('type' in res && res.type === "html") {
      setPreviewSource({ mode: 'html', html: res.html });
    }
    setPendingVersion(null);
  };

  const handleFileSelect = (path: string) => {
    setSelectedFile(path);
  };

  return (<div className="h-screen flex flex-col bg-gray-100">
    <main className="flex-1 flex flex-col overflow-hidden">
      <ResizableLayout 
        leftPanel={<ChatPanelV2 
          messages={messages} 
          isLoading={isLoading} 
          currentBlocks={currentBlocks} 
          completedTurns={completedTurns} 
          onSendMessage={sendMessage} 
          onStopGeneration={stopGeneration} 
          sessionCount={111}
        />} 
        rightPanel={<PreviewPanel sessionId={sessionId} previewSource={previewSource} files={files as any} selectedFile={selectedFile} onFileSelect={handleFileSelect} />} 
      />
    </main>

    {pendingVersion && (<BaseConfirmDialog targetVersion={pendingVersion} currentBase={currentBase} onConfirm={handleConfirmSwitch} onCancel={() => setPendingVersion(null)} />)}
  </div>);
}
