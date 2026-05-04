/**
 * ThinkingPanel - 思维链展示组件
 * 接收 SSE 的 thinking_start / thinking_delta / thinking_end 事件
 * 以可折叠卡片形式展示 Agent 思考过程
 */

import React, { useState, useRef, useEffect } from 'react';
import { Brain, ChevronDown, ChevronRight } from 'lucide-react';

import type { ThinkingBlock } from '../services/sse/types';

// ========== Props ==========

interface ThinkingPanelProps {
  block: ThinkingBlock;
}

// ========== Typewriter 效果组件 ==========

interface TypewriterProps {
  text: string;
  speed?: number; // 每字 ms，默认 10
}

function Typewriter({ text, speed = 10 }: TypewriterProps) {
  const [displayedText, setDisplayedText] = useState('');
  const [isComplete, setIsComplete] = useState(false);
  const indexRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    setDisplayedText('');
    setIsComplete(false);
    indexRef.current = 0;

    function tick() {
      if (indexRef.current < text.length) {
        // 每次追加一个字符或一小段
        const chunkSize = text.length > 200 ? Math.ceil(text.length / 100) : 1;
        indexRef.current = Math.min(indexRef.current + chunkSize, text.length);
        setDisplayedText(text.slice(0, indexRef.current));
        timerRef.current = setTimeout(tick, speed);
      } else {
        setIsComplete(true);
      }
    }

    timerRef.current = setTimeout(tick, speed);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [text, speed]);

  return (
    <span>
      {displayedText}
      {!isComplete && (
        <span className="inline-block w-1 h-4 ml-0.5 align-middle bg-blue-400 animate-pulse" />
      )}
    </span>
  );
}

// ========== Markdown 渲染器（轻量级）==========

function MarkdownRenderer({ content }: { content: string }) {
  // 简单的 markdown → HTML 转换（不需要引入重型库）
  // 只处理：粗体、斜体、行内代码、列表、标题
  const html = content
    .replace(/^### (.+)$/gm, '<h3 class="text-sm font-semibold mt-3 mb-1">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 class="text-base font-bold mt-3 mb-1">$1</h2>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code class="px-1 py-0.5 rounded bg-blue-100 text-blue-700 text-xs font-mono">$1</code>')
    .replace(/^- (.+)$/gm, '<li class="ml-4 list-disc">$1</li>')
    .replace(/\n/g, '<br/>');

  return (
    <div
      className="text-sm leading-relaxed"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

// ========== 主组件 ==========

export function ThinkingPanel({ block }: ThinkingPanelProps) {
  const [expanded, setExpanded] = useState(block.status === 'streaming');
  const contentRef = useRef<HTMLDivElement>(null);

  // 流式内容超长时截断显示
  const isLongContent = block.content.length > 2000;
  const displayContent = isLongContent ? block.content.slice(0, 2000) + '\n\n...(内容过长，点击展开查看全部)' : block.content;

  return (
    <div className="thinking-panel border-l-2 border-blue-400 bg-blue-50/50 rounded-r-lg p-4">
      {/* 头部：图标 + 状态 + 折叠按钮 */}
      <header
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 cursor-pointer select-none"
      >
        <Brain size={16} className="shrink-0 text-blue-600" />

        {/* 状态文字 */}
        <span className={`text-sm font-medium ${
          block.status === 'streaming' ? 'text-blue-700' : 'text-slate-600'
        }`}>
          {block.status === 'streaming' ? (
            <>
              正在思考...
              <span className="inline-flex gap-1 ml-2">
                <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce [animation-delay:0ms]" />
                <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce [animation-delay:150ms]" />
                <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce [animation-delay:300ms]" />
              </span>
            </>
          ) : (
            '思考完成'
          )}
        </span>

        {/* 折叠态摘要 */}
        {block.summary && !expanded && (
          <span className="ml-2 text-xs text-slate-500 italic truncate max-w-[200px]">
            {block.summary}
          </span>
        )}

        {/* 展开/收起图标 */}
        {expanded ? (
          <ChevronDown size={14} className="ml-auto shrink-0 text-slate-400" />
        ) : (
          <ChevronRight size={14} className="ml-auto shrink-0 text-slate-400" />
        )}
      </header>

      {/* 内容区 */}
      {expanded && (
        <div ref={contentRef} className="mt-2 pl-2 border-l border-blue-200">
          {block.status === 'streaming' ? (
            <div className="text-sm text-slate-600 leading-relaxed">
              <Typewriter text={displayContent} />
            </div>
          ) : (
            <MarkdownRenderer content={displayContent} />
          )}

          {/* 超长内容提示 */}
          {isLongContent && (
            <button
              onClick={() => setExpanded(true)}
              className="mt-2 text-xs text-blue-500 hover:text-blue-700"
            >
              展开完整内容 ({block.content.length.toLocaleString()} 字)
            </button>
          )}

          {/* 完成时间 */}
          {block.status === 'complete' && block.completedAt && block.startedAt && (
            <p className="mt-2 text-[11px] text-slate-400">
              耗时：{((block.completedAt - block.startedAt) / 1000).toFixed(1)}s
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export default ThinkingPanel;
