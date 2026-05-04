/**
 * ToolCard - 工具调用卡片组件（P1.15）
 *
 * 接收 SSE 的 tool_call:start / tool_call:end 事件
 * 以紧凑卡片形式展示 Agent 调用了哪个工具、参数是什么、结果如何
 * 默认折叠只显示工具名+状态，点击展开查看参数和错误详情
 */

import React, { useState, useMemo } from 'react';
import { Wrench, ChevronRight, CheckCircle, XCircle, Loader2, AlertTriangle } from 'lucide-react';

import type { ToolCallBlock } from '../services/sse/types';

// ========== Props ==========

interface ToolCardProps {
  tool: ToolCallBlock;
}

// ========== 参数预览子组件（截断大 JSON）==========

function ParamPreview({ input }: { input: Record<string, unknown> }) {
  const entries = Object.entries(input);

  // 截断预览：每个值最多显示 80 字符
  const truncatedEntries = useMemo(() => {
    return entries.map(([key, value]) => {
      const raw = typeof value === 'string' ? value : JSON.stringify(value);
      const preview = raw.length > 80 ? raw.slice(0, 80) + '…' : raw;
      return [key, preview, raw] as const;
    });
  }, [entries]);

  const totalSize = JSON.stringify(input).length;

  return (
    <div className="params-preview">
      {/* 预览模式：top-level keys + 截断值 */}
      <div className="space-y-1.5">
        {truncatedEntries.map(([key, preview, raw]) => (
          <div key={key} className="flex gap-2 text-xs font-mono">
            <span className="text-indigo-600 font-semibold shrink-0">{key}:</span>
            <span className="text-slate-600 break-all">{preview}</span>
          </div>
        ))}
      </div>

      {/* 超大参数提示 */}
      {totalSize > 2048 && (
        <p className="mt-2 text-[11px] text-slate-400 italic">
          共 {totalSize.toLocaleString()} 字符，下方显示完整内容
        </p>
      )}

      {/* 完整 JSON */}
      <details className="mt-2 group">
        <summary className="cursor-pointer text-xs text-slate-500 hover:text-slate-700 select-none list-none flex items-center gap-1">
          <ChevronRight size={12} className="transition-transform group-open:rotate-90" />
          完整 JSON
        </summary>
        <pre className="params-json mt-2 p-2.5 bg-slate-900 text-slate-100 rounded-md text-[11px] leading-relaxed overflow-auto max-h-48">
          {JSON.stringify(input, null, 2)}
        </pre>
      </details>
    </div>
  );
}

// ========== 主组件 ==========

export function ToolCard({ tool }: ToolCardProps) {
  const [showDetails, setShowDetails] = useState(false);
  const isRunning = tool.status === 'running';
  const isSuccess = tool.status === 'success';
  const isError = tool.status === 'error';

  // 状态样式映射
  const statusConfig = {
    running: {
      container: 'bg-amber-50/80 border-amber-300',
      badge: 'bg-amber-100 text-amber-700',
      icon: <Loader2 size={14} className="animate-spin text-amber-600" />,
      label: '运行中...',
    },
    success: {
      container: 'bg-green-50/80 border-green-300',
      badge: 'bg-green-100 text-green-700',
      icon: <CheckCircle size={14} className="text-green-600" />,
      label: tool.durationMs ? `${tool.durationMs}ms` : '成功',
    },
    error: {
      container: 'bg-red-50/80 border-red-300',
      badge: 'bg-red-100 text-red-700',
      icon: <XCircle size={14} className="text-red-600" />,
      label: '失败',
    },
  };

  const config = statusConfig[tool.status];

  return (
    <div className={`tool-card rounded-lg border p-3 transition-colors ${config.container}`}>
      {/* 主行：图标 + 工具名 + 状态标签 + 展开/收起 */}
      <div
        className="main-row flex items-center gap-2 cursor-pointer select-none"
        onClick={() => setShowDetails(!showDetails)}
      >
        {/* 工具图标 */}
        <Wrench size={14} className={`shrink-0 ${
          isRunning ? 'text-amber-600' : isSuccess ? 'text-green-600' : 'text-red-600'
        }`} />

        {/* 工具名称（等宽字体） */}
        <code className="font-mono text-sm text-slate-700 truncate max-w-[180px]">
          {tool.name}
        </code>

        {/* 状态 Badge */}
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium ${config.badge}`}>
          {isRunning && config.icon}
          {!isRunning && config.icon}
          {config.label}
        </span>

        {/* 呼吸动画（运行中） */}
        {isRunning && (
          <span className="flex gap-0.5 ml-1">
            <span className="w-1 h-1 bg-amber-400 rounded-full animate-pulse [animation-delay:0ms]" />
            <span className="w-1 h-1 bg-amber-400 rounded-full animate-pulse [animation-delay:400ms]" />
            <span className="w-1 h-1 bg-amber-400 rounded-full animate-pulse [animation-delay:800ms]" />
          </span>
        )}

        {/* 展开/收起箭头 */}
        <ChevronRight
          size={14}
          className={`ml-auto shrink-0 text-slate-400 transition-transform duration-200 ${
            showDetails ? 'rotate-90' : ''
          }`}
        />
      </div>

      {/* 展开详情区域 */}
      {showDetails && (
        <div className="details mt-3 pl-6 border-l-2 border-slate-200 space-y-3">
          {/* 输入参数 */}
          {tool.input && Object.keys(tool.input).length > 0 && (
            <div>
              <h4 className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
                输入参数
              </h4>
              <ParamPreview input={tool.input} />
            </div>
          )}

          {/* 错误信息 */}
          {isError && tool.error && (
            <div className="error-msg flex gap-2 p-2.5 bg-red-100 rounded-md">
              <AlertTriangle size={14} className="shrink-0 text-red-600 mt-0.5" />
              <p className="text-xs text-red-700 whitespace-pre-wrap break-words">
                {tool.error}
              </p>
            </div>
          )}

          {/* 时间信息 */}
          {(isSuccess || isError) && tool.startedAt && tool.endedAt && (
            <div className="time-info text-[11px] text-slate-400">
              开始于 {new Date(tool.startedAt).toLocaleTimeString()}
              {tool.durationMs !== undefined && <> · 耗时 {(tool.durationMs / 1000).toFixed(2)}s</>}
            </div>
          )}

          {/* 运行中时长 */}
          {isRunning && tool.startedAt && !tool.endedAt && (
            <RunningDuration startedAt={tool.startedAt} />
          )}
        </div>
      )}
    </div>
  );
}

// ========== 运行中实时计时子组件 ==========

function RunningDuration({ startedAt }: { startedAt: number }) {
  const [elapsed, setElapsed] = useState(0);

  React.useEffect(() => {
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startedAt) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [startedAt]);

  const mins = Math.floor(elapsed / 60);
  const secs = elapsed % 60;

  return (
    <div className="time-info flex items-center gap-1.5 text-[11px] text-amber-600">
      <Loader2 size={12} className="animate-spin" />
      已运行 {mins > 0 ? `${mins}m ` : ''}{secs}s
    </div>
  );
}

export default ToolCard;
