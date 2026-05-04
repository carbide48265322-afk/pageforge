/**
 * Error Toast - 用于网络类瞬时错误的弹窗提示
 */

import React from 'react';
import { useErrorContext } from './ErrorStore';
import type { AppError } from './types';
import { X, RefreshCw } from 'lucide-react';

interface ErrorToastProps {
  error: AppError;
  onDismiss: (id: string) => void;
  onRetry?: (id: string) => void;
}

export function ErrorToast({ error, onDismiss, onRetry }: ErrorToastProps) {
  return (
    <div
      className="error-toast group relative flex items-center gap-3 rounded-lg border px-4 py-3 shadow-lg transition-all"
      style={{
        animation: 'slideInRight 0.3s ease-out',
        borderColor: error.recoverable ? '#f59e0b' : '#ef4444',
        backgroundColor: error.recoverable ? '#fffbeb' : '#fef2f2',
      }}
    >
      {/* 图标 */}
      <div
        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-bold"
        style={{
          backgroundColor: error.recoverable ? '#f59e0b' : '#ef4444',
          color: '#ffffff',
        }}
      >
        {error.recoverable ? '!' : '✕'}
      </div>

      {/* 消息内容 */}
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium" style={{ color: '#1f2937' }}>
          {error.message}
        </p>
        {error.detail && (
          <p className="mt-1 text-xs truncate" style={{ color: '#6b7280' }}>
            {error.detail}
          </p>
        )}
      </div>

      {/* 操作按钮 */}
      <div className="flex items-center gap-2">
        {error.recoverable && onRetry && (
          <button
            onClick={() => onRetry(error.id)}
            className="flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium transition-colors hover:bg-black/5"
            style={{ color: '#2563eb' }}
          >
            <RefreshCw size={12} />
            重试
          </button>
        )}

        {/* 关闭按钮 */}
        <button
          onClick={() => onDismiss(error.id)}
          className="rounded p-1 opacity-50 transition-opacity hover:opacity-100"
        >
          <X size={14} />
        </button>
      </div>
    </div>
  );
}

/** Toast 容器（管理多个 toast 的展示） */
export function ErrorToastContainer() {
  const { state, dismissError, retryError } = useErrorContext();

  // 只显示未被关闭的、最近的 5 个错误
  const visibleErrors = state.errors
    .filter(e => !e.dismissed)
    .slice(-5);

  if (visibleErrors.length === 0) return null;

  return (
    <div className="fixed right-4 top-4 z-[9999] flex flex-col gap-2">
      {visibleErrors.map(error => (
        <ErrorToast
          key={error.id}
          error={error}
          onDismiss={dismissError}
          onRetry={retryError ? (id) => retryError(id, async () => {}) : undefined}
        />
      ))}
    </div>
  );
}
