/**
 * Error Card - 内联错误卡片
 * 用于展示生成过程中的错误（嵌入对话流中）
 */

import React from 'react';
import type { AppError, ErrorCategory } from './types';
import { AlertTriangle, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react';

interface ErrorCardProps {
  error: AppError;
  onRetry?: (id: string) => void;
  onFallback?: () => void;
  children?: React.ReactNode;
}

export function ErrorCard({ error, onRetry, onFallback, children }: ErrorCardProps) {
  const [showDetail, setShowDetail] = React.useState(false);

  // 根据类别选择颜色
  const colorMap: Record<ErrorCategory, { bg: string; border: string; icon: string }> = {
    [ErrorCategory.NETWORK]:      { bg: '#fef3c7', border: '#f59e0b', icon: '🔌' },
    [ErrorCategory.WEBCONTAINER]:{ bg: '#ede9fe', border: '#8b5cf6', icon: '📦' },
    [ErrorCategory.DEPENDENCY]:   { bg: '#fef9c3', border: '#eab308', icon: '📦' },
    [ErrorCategory.GENERATION]:   { bg: '#fee2e2', border: '#ef4444', icon: '⚙️' },
    [ErrorCategory.FILESYSTEM]:   { bg: '#fce7f3', border: '#ec4899', icon: '📁' },
    [ErrorCategory.SERVER]:       { bg: '#e0f2fe', border: '#0ea5e9', icon: '🖥️' },
    [ErrorCategory.UNKNOWN]:      { bg: '#f5f5f4', border: '#a8a29e', icon: '❓' },
  };

  const colors = colorMap[error.category] || colorMap[ErrorCategory.UNKNOWN];

  return (
    <div
      className="error-card rounded-lg border p-3"
      style={{ backgroundColor: colors.bg, borderColor: colors.border }}
    >
      {/* 头部：图标 + 消息 + 操作 */}
      <div className="flex items-start gap-2">
        <span className="text-base">{colors.icon}</span>

        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-gray-800">{error.message}</p>
          <p className="text-xs text-gray-500 mt-0.5">
            [{error.code}] {new Date(error.timestamp).toLocaleTimeString()}
          </p>
        </div>
      </div>

      {/* 展开详情 */}
      {(error.detail || showDetail) && (
        <button
          onClick={() => setShowDetail(!showDetail)}
          className="mt-2 flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700"
        >
          {showDetail ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          {showDetail ? '收起详情' : '查看详情'}
        </button>
      )}

      {showDetail && error.detail && (
        <pre
          className="mt-2 overflow-x-auto rounded bg-black/5 p-2 text-xs leading-relaxed text-gray-600 whitespace-pre-wrap"
        >
          {error.detail}
        </pre>
      )}

      {/* 子内容（如嵌套的组件） */}
      {children}

      {/* 操作按钮行 */}
      <div className="mt-3 flex items-center gap-2">
        {error.recoverable && onRetry && (
          <button
            onClick={() => onRetry(error.id)}
            className="inline-flex items-center gap-1 rounded-md px-3 py-1.5 text-xs font-medium transition-colors hover:bg-white/50"
            style={{
              backgroundColor: error.recoverable ? colors.border : undefined,
              color: '#ffffff',
            }}
          >
            <RefreshCw size={12} />
            重试
          </button>
        )}
        {onFallback && (
          <button
            onClick={onFallback}
            className="inline-flex items-center gap-1 rounded-md border px-3 py-1.5 text-xs font-medium transition-colors hover:bg-black/5"
            style={{ borderColor: colors.border }}
          >
            降级方案
          </button>
        )}
      </div>
    </div>
  );
}

// ========== 全局错误边界 ==========

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class GlobalErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="flex min-h-screen items-center justify-center p-8">
          <div className="max-w-md text-center">
            <AlertTriangle size={48} className="mx-auto mb-4 text-red-500" />
            <h2 className="text-lg font-semibold text-gray-800">应用出现异常</h2>
            <p className="mt-2 text-sm text-gray-500">
              {this.state.error?.message || '发生了未预期的错误'}
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="mt-6 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              重新加载
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
