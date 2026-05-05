import { useState, useRef, useEffect } from "react";
import { Send, ChevronDown, ChevronRight, Wrench, Check, Loader2, FileText, Terminal, Plus, ArrowLeft, Rocket } from "lucide-react";
import type { Message } from "../services/api";
import type { RenderBlockV2, IntentResultV2, PlanStepV2, FileInfo, StatusInfo } from "../hooks/useSSEv2";
import { MessageBubble } from "./MessageBubble";

interface ChatPanelV2Props {
  messages: Message[];
  isLoading: boolean;
  currentBlocks: RenderBlockV2[];
  completedTurns: { userMsg: Message; blocks: RenderBlockV2[] }[];
  onSendMessage: (content: string) => void;
  sessionCount?: number;
}

export function ChatPanelV2({
  messages,
  isLoading,
  currentBlocks,
  completedTurns,
  onSendMessage,
  sessionCount = 0,
}: ChatPanelV2Props) {
  const [input, setInput] = useState("");
  const [isAtBottom, setIsAtBottom] = useState(true);
  const [isComposing, setIsComposing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

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

  const renderBlocks = (blocks: RenderBlockV2[]) => {
    return (
      <>
        {blocks.map((block) => (
          <div key={block.id}>
            {block.type === "intent" && block.intent && (
              <IntentPanel intent={block.intent} />
            )}

            {block.type === "thinking" && (
              <ThinkingPanel content={block.content} status={block.status} />
            )}

            {block.type === "plan" && block.plan_steps && (
              <PlanPanel steps={block.plan_steps} />
            )}

            {block.type === "tool_call" && (
              <ToolCard
                tool={block.tool || ""}
                status={block.status}
              />
            )}

            {(block.type === "file_created" || block.type === "file_updated") && block.file && (
              <FileNotification
                type={block.type}
                file={block.file}
              />
            )}

            {block.type === "status" && block.status_info && (
              <StatusNotification statusInfo={block.status_info} />
            )}

            {block.type === "command_output" && (
              <CommandOutput content={block.content} />
            )}

            {block.type === "style_selected" && (
              <StyleSelected content={block.content} />
            )}

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
    <div className="flex flex-col h-full bg-gray-50">
      <header className="flex items-center justify-between px-4 py-2.5 shrink-0">
        <div className="flex items-center gap-2">
          <button className="flex items-center justify-center size-7 rounded-lg hover:bg-gray-200 transition-colors">
            <ArrowLeft size={16} className="text-gray-600" />
          </button>
          <div className="flex items-center gap-2">
            <div className="flex items-center justify-center w-7 h-7 rounded-md bg-black">
              <Rocket size={14} className="text-white" />
            </div>
            <span className="font-semibold text-gray-900 text-sm">PageForge</span>
          </div>
        </div>
        {sessionCount > 0 && (
          <div className="flex items-center gap-2">
            <span className="flex items-center justify-center w-7 h-7 rounded-full bg-gray-800 text-white text-xs font-medium">
              {sessionCount}
            </span>
          </div>
        )}
      </header>
      <div ref={scrollContainerRef} className="flex-1 overflow-y-auto px-4 py-3">
        {completedTurns.length === 0 && currentBlocks.length === 0 && !isLoading && (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mb-4">
              <Terminal size={24} className="text-gray-300" />
            </div>
            <p className="text-sm">描述你想要的项目，Agent 将为你生成</p>
          </div>
        )}

        {completedTurns.map((turn) => (
          <div key={turn.userMsg.id} className="mb-4">
            <MessageBubble message={turn.userMsg} />
            {turn.blocks.length > 0 && renderBlocks(turn.blocks)}
          </div>
        ))}

        {isLoading && messages.length > 0 && (
          <div className="mb-4">
            <MessageBubble message={messages[messages.length - 1]} />
          </div>
        )}

        {currentBlocks.length > 0 && renderBlocks(currentBlocks)}

        <div ref={messagesEndRef} />
      </div>

      <div className="px-4 py-3">
        <div className="bg-gray-100 border border-gray-200 p-3 flex flex-col gap-3 relative rounded-2xl">
          <input
            accept="image/png,.png,image/jpeg,.jpg,.jpeg,image/gif,.gif,image/webp,.webp,image/bmp,.bmp,video/*,.mp4,.webm,.ogg,.mov,application/pdf,.pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,.docx"
            multiple
            type="file"
            className="hidden"
            aria-hidden="true"
          />
          <div className="flex relative flex-col cursor-text">
            <div className="relative">
              <div style={{ minHeight: '64px', maxHeight: '300px', overflowY: 'auto', position: 'relative' }}>
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  onCompositionStart={() => setIsComposing(true)}
                  onCompositionEnd={() => setIsComposing(false)}
                  placeholder="和 Meoo 一起创作..."
                  rows={3}
                  className="w-full resize-none px-4 py-3 text-sm bg-transparent
                    focus:outline-none focus:ring-0
                    disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                  disabled={isLoading}
                  style={{ minHeight: '64px', maxHeight: '300px' }}
                />
              </div>
            </div>
          </div>
          <div className="flex gap-1 justify-between items-end w-full">
            <div className="flex items-center gap-1">
              <button className="flex items-center justify-center rounded-lg size-8 bg-transparent hover:bg-gray-100 transition-colors cursor-pointer">
                <Plus size={16} className="text-gray-600" />
              </button>
              <button className="flex items-center justify-center rounded-lg size-8 bg-transparent hover:bg-gray-100 transition-colors cursor-pointer">
                <Loader2 size={16} className={isLoading ? "animate-spin text-purple-500" : "text-gray-600"} />
              </button>
              <button className="flex items-center justify-center rounded-lg size-8 bg-transparent hover:bg-gray-100 transition-colors cursor-pointer">
                <Wrench size={14} className="text-gray-500" />
              </button>
            </div>
            <div className="flex gap-1 items-center shrink-0">
              {isLoading && (
                <div className="flex items-center">
                  <div className="relative w-6 flex items-center justify-center">
                    <div className="relative cursor-pointer flex items-center justify-center rounded-full" style={{ width: '16px', height: '16px' }}>
                      <svg width="16" height="16" viewBox="0 0 16 16" className="block" aria-hidden="true">
                        <circle cx="8" cy="8" r="6" fill="none" stroke="#E9EAEB" strokeWidth="2"/>
                        <g transform="rotate(-90 8 8)">
                          <circle cx="8" cy="8" r="6" fill="none" stroke="#a855f7" strokeWidth="2" strokeLinecap="round" strokeDasharray="15.98 21.72" strokeDashoffset="0"/>
                        </g>
                      </svg>
                    </div>
                  </div>
                </div>
              )}
              <div className="flex relative items-center shrink-0">
                <div className="flex items-center justify-center size-8 shrink-0 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors">
                  <span className="text-base leading-none w-4 h-4 text-gray-500">∞</span>
                </div>
              </div>
              <button
                onClick={handleSubmit}
                disabled={!input.trim() || isLoading}
                className="flex justify-center items-center text-sm font-medium text-white rounded-lg
                  transition-colors duration-200 ease-in-out w-8 h-8 shrink-0
                  disabled:cursor-not-allowed disabled:opacity-50
                  bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
                title="发送"
              >
                <Send size={14} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function IntentPanel({ intent }: { intent: IntentResultV2 }) {
  return (
    <div className="mb-3 p-3 bg-blue-50 rounded-lg border border-blue-100 text-xs">
      <div className="flex items-center gap-2 text-blue-700 font-medium mb-2">
        <Terminal size={12} />
        <span>意图识别</span>
      </div>
      <div className="text-gray-600 space-y-1">
        <div>类型: <span className="font-medium text-gray-800">{intent.intent}</span></div>
        <div>置信度: <span className="font-medium text-gray-800">{(intent.confidence * 100).toFixed(0)}%</span></div>
        {intent.tags?.length && intent.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {intent.tags.map((tag: string, i: number) => (
              <span key={i} className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-md text-xs">
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ThinkingPanel({ content, status }: { content: string; status: string }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="mb-3">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-xs text-gray-400 hover:text-gray-600 transition-colors duration-200"
      >
        <Loader2 size={12} className={status === "streaming" ? "animate-spin text-gray-400" : "text-gray-300"} />
        <span>Agent 思考中</span>
        {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
      </button>
      {isExpanded && (
        <div className="mt-2 bg-gray-50 rounded-lg px-4 py-3 text-xs text-gray-600 whitespace-pre-wrap border border-gray-100">
          {content}
        </div>
      )}
    </div>
  );
}

function PlanPanel({ steps }: { steps: PlanStepV2[] }) {
  return (
    <div className="mb-3 p-3 bg-emerald-50 rounded-lg border border-emerald-100">
      <div className="text-xs font-medium text-emerald-700 mb-2">执行计划</div>
      <div className="space-y-1.5">
        {steps.map((step) => (
          <div key={step.step} className="flex items-center gap-2 text-xs">
            {step.status === "done" ? (
              <Check size={12} className="text-emerald-500 flex-shrink-0" />
            ) : step.status === "in_progress" ? (
              <Loader2 size={12} className="animate-spin text-blue-500 flex-shrink-0" />
            ) : (
              <div className="w-3 h-3 rounded-full border border-gray-300 flex-shrink-0" />
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

function ToolCard({ tool, status }: { tool: string; status: string }) {
  return (
    <div className="mb-2 flex items-center gap-2 text-xs text-gray-500 px-2 py-1.5">
      <Wrench size={12} className="text-gray-400" />
      <span className="font-medium">{tool}</span>
      {status === "done" ? (
        <Check size={12} className="text-emerald-500" />
      ) : (
        <Loader2 size={12} className="animate-spin text-blue-500" />
      )}
    </div>
  );
}

function FileNotification({ type, file }: { type: string; file: FileInfo }) {
  return (
    <div className="mb-2 flex items-center gap-2 text-xs text-blue-600 bg-blue-50 rounded-lg px-3 py-2">
      <FileText size={12} />
      <span>
        {type === "file_created" ? "创建" : "更新"}文件: <span className="font-medium">{file.path}</span>
      </span>
    </div>
  );
}

function CommandOutput({ content }: { content: string }) {
  return (
    <div className="mb-2 font-mono text-xs text-gray-400 bg-gray-900 rounded-lg px-3 py-2 whitespace-pre-wrap">
      {content}
    </div>
  );
}

function StyleSelected({ content }: { content: string }) {
  return (
    <div className="mb-2 flex items-center gap-2 text-xs text-purple-600 bg-purple-50 rounded-lg px-3 py-2">
      <span>🎨 {content}</span>
    </div>
  );
}

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
    <div className="mb-2 flex items-center gap-2 text-xs text-gray-500 px-2 py-1.5">
      <Terminal size={12} className="text-gray-400" />
      <span className="font-medium">{statusLabels[statusInfo.status] || statusInfo.status}</span>
      {statusInfo.message && (
        <span className="text-gray-400">- {statusInfo.message}</span>
      )}
    </div>
  );
}
