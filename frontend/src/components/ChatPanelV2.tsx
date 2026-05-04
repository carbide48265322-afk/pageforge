import { useState, useRef, useEffect } from "react";
import { Send, Square, ChevronDown, ChevronRight, Wrench, Check, Loader2, FileText, FolderOpen, Terminal } from "lucide-react";
import type { Message } from "../services/api";
import type { RenderBlockV2, IntentResult, PlanStep, FileInfo, StatusInfo } from "../hooks/useSSEv2";
import { MessageBubble } from "./MessageBubble";

/** ChatPanelV2 组件的 props（支持新消息类型） */
interface ChatPanelV2Props {
  messages: Message[];
  isLoading: boolean;
  currentBlocks: RenderBlockV2[];
  completedTurns: { userMsg: Message; blocks: RenderBlockV2[] }[];
  latestVersion: number;
  onSendMessage: (content: string) => void;
  onStopGeneration: () => void;
  onPreview: () => void;
}

/**
 * 聊天面板 V2 组件
 * 支持新消息类型：intent/thinking/plan/file/status
 * 与旧 ChatPanel.tsx 并存，不修改旧文件
 */
export function ChatPanelV2({
  messages,
  isLoading,
  currentBlocks,
  completedTurns,
  latestVersion,
  onSendMessage,
  onStopGeneration,
  onPreview,
}: ChatPanelV2Props) {
  const [input, setInput] = useState("");
  const [isAtBottom, setIsAtBottom] = useState(true);
  const [isComposing, setIsComposing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // 智能滚动
  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsAtBottom(entry.isIntersecting);
      },
      { root: container, threshold: 0 },
    );

    const anchor = messagesEndRef.current;
    if (anchor) observer.observe(anchor);

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (isLoading) {
      messagesEndRef.current?.scrollIntoView({ behavior: "instant" });
    } else if (isAtBottom) {
      messagesEndRef.current?.scrollIntoView({ behavior: "instant" });
    }
  }, [messages, currentBlocks, isLoading, isAtBottom]);

  const handleSubmit = () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;
    onSendMessage(trimmed);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey && !isComposing) {
      e.preventDefault();
      handleSubmit();
    }
  };

  /** 渲染块列表（支持新类型） */
  const renderBlocks = (blocks: RenderBlockV2[]) => {
    return (
      <>
        {blocks.map((block) => (
          <div key={block.id}>
            {/* 意图识别 */}
            {block.type === "intent" && block.intent && (
              <IntentPanel intent={block.intent} />
            )}

            {/* 思维链 */}
            {block.type === "thinking" && (
              <ThinkingPanel content={block.content} status={block.status} />
            )}

            {/* 计划 */}
            {block.type === "plan" && block.plan_steps && (
              <PlanPanel steps={block.plan_steps} />
            )}

            {/* 工具调用 */}
            {block.type === "tool_call" && (
              <ToolCard
                tool={block.tool || ""}
                status={block.status}
              />
            )}

            {/* 文件创建/更新 */}
            {(block.type === "file_created" || block.type === "file_updated") && block.file && (
              <FileNotification
                type={block.type}
                file={block.file}
              />
            )}

            {/* 状态更新 */}
            {block.type === "status" && block.status_info && (
              <StatusNotification statusInfo={block.status_info} />
            )}

            {/* 文本（兼容旧类型） */}
            {(block.type === "text" || block.type === "generation") && (
              <MessageBubble
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
            )}
          </div>
        ))}
      </>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* 消息列表区域 */}
      <div ref={scrollContainerRef} className="flex-1 overflow-y-auto px-4 py-4">
        {completedTurns.length === 0 && currentBlocks.length === 0 && !isLoading && (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm">
            描述你想要的项目，Agent 将为你生成
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

        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <div className="border-t border-gray-200 px-4 py-3">
        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            onCompositionStart={() => setIsComposing(true)}
            onCompositionEnd={() => setIsComposing(false)}
            placeholder="描述你想要的项目..."
            rows={1}
            className="flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm
              focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
              disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={isLoading}
          />

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

// ========== 子组件定义 ==========

/** 意图识别面板 */
function IntentPanel({ intent }: { intent: IntentResult }) {
  return (
    <div className="mb-2 p-3 bg-blue-50 rounded-lg border border-blue-200 text-xs">
      <div className="flex items-center gap-2 text-blue-600 font-medium mb-1">
        <Terminal size={12} />
        <span>意图识别</span>
      </div>
      <div className="text-gray-600">
        <div>类型: {intent.intent}</div>
        <div>置信度: {(intent.confidence * 100).toFixed(0)}%</div>
        {intent.tags.length > 0 && (
          <div className="flex gap-1 mt-1">
            {intent.tags.map((tag, i) => (
              <span key={i} className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded">
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/** 思维链面板（可折叠） */
function ThinkingPanel({ content, status }: { content: string; status: string }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="mb-2">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-xs text-gray-400 hover:text-gray-600"
      >
        <Loader2 size={12} className={status === "streaming" ? "animate-spin" : ""} />
        <span>Agent 思考中</span>
        {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
      </button>
      {isExpanded && (
        <div className="mt-1 bg-gray-50 rounded-lg px-3 py-2 text-xs text-gray-600 whitespace-pre-wrap">
          {content}
        </div>
      )}
    </div>
  );
}

/** 计划面板 */
function PlanPanel({ steps }: { steps: PlanStep[] }) {
  return (
    <div className="mb-2 p-3 bg-green-50 rounded-lg border border-green-200">
      <div className="text-xs font-medium text-green-700 mb-2">执行计划</div>
      <div className="space-y-1">
        {steps.map((step) => (
          <div key={step.step} className="flex items-center gap-2 text-xs">
            {step.status === "done" ? (
              <Check size={12} className="text-green-500" />
            ) : step.status === "in_progress" ? (
              <Loader2 size={12} className="animate-spin text-blue-500" />
            ) : (
              <div className="w-3 h-3 rounded-full border border-gray-300" />
            )}
            <span className={step.status === "done" ? "text-gray-400 line-through" : "text-gray-600"}>
              {step.step}. {step.description}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/** 工具调用卡片 */
function ToolCard({ tool, status }: { tool: string; status: string }) {
  return (
    <div className="mb-2 flex items-center gap-2 text-xs text-gray-500 px-1">
      <Wrench size={12} />
      <span>{tool}</span>
      {status === "done" ? (
        <Check size={12} className="text-green-500" />
      ) : (
        <Loader2 size={12} className="animate-spin text-blue-500" />
      )}
    </div>
  );
}

/** 文件通知 */
function FileNotification({ type, file }: { type: string; file: FileInfo }) {
  return (
    <div className="mb-2 flex items-center gap-2 text-xs text-blue-600 bg-blue-50 rounded px-2 py-1">
      <FileText size={12} />
      <span>
        {type === "file_created" ? "创建" : "更新"}文件: {file.path}
      </span>
    </div>
  );
}

/** 状态通知 */
function StatusNotification({ statusInfo }: { statusInfo: StatusInfo }) {
  const statusLabels: Record<string, string> = {
    init: "初始化项目",
    installing: "安装依赖中",
    install_done: "依赖安装完成",
    generation_done: "代码生成完成",
    starting_dev: "启动开发服务器",
    preview_ready: "预览就绪",
  };

  return (
    <div className="mb-2 flex items-center gap-2 text-xs text-gray-500 px-1">
      <Terminal size={12} />
      <span>{statusLabels[statusInfo.status] || statusInfo.status}</span>
      {statusInfo.message && (
        <span className="text-gray-400">- {statusInfo.message}</span>
      )}
    </div>
  );
}
