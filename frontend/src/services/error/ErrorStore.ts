/**
 * 错误状态管理（Context Store）
 * 轻量级，不需要 Redux/Zustand，Context 够用
 */

import React, { createContext, useContext, useReducer, useCallback } from 'react';
import type { AppError, ErrorState, ErrorCategory } from './types';

// ========== Action Types ==========

type ErrorAction =
  | { type: 'ADD_ERROR'; error: AppError }
  | { type: 'DISMISS_ERROR'; id: string }
  | { type: 'RETRY_ERROR'; id: string; action: () => Promise<void> }
  | { type: 'CLEAR_RESOLVED' };

// ========== Reducer ==========

function calculateActiveError(errors: AppError[]): AppError | null {
  // 找到第一个未被关闭且未处理的错误（按时间倒序，最新的优先）
  for (let i = errors.length - 1; i >= 0; i--) {
    const err = errors[i];
    if (!err.dismissed && err.recoverable) return err;
  }

  // 如果没有可恢复的错误，找第一个未关闭的
  for (let i = errors.length - 1; i >= 0; i--) {
    if (!errors[i].dismissed) return errors[i];
  }

  return null;
}

const initialState: ErrorState = {
  errors: [],
  activeError: null,
};

function errorReducer(state: ErrorState, action: ErrorAction): ErrorState {
  switch (action.type) {
    case 'ADD_ERROR': {
      const newErrors = [...state.errors, action.error];
      return {
        ...state,
        errors: newErrors,
        activeError: calculateActiveError(newErrors),
      };
    }

    case 'DISMISS_ERROR': {
      const newErrors = state.errors.map(err =>
        err.id === action.id ? { ...err, dismissed: true } : err,
      );
      return {
        ...state,
        errors: newErrors,
        activeError: calculateActiveError(newErrors),
      };
    }

    case 'RETRY_ERROR':
      // 触发重试，由调用方处理成功/失败后更新状态
      action.action();
      return state;

    case 'CLEAR_RESOLVED': {
      const newErrors = state.errors.filter(
        err => !err.dismissed && (err.recoverable || !err.dismissed),
      );
      // 实际上只保留未被关闭的错误
      const kept = state.errors.filter(err => !err.dismissed);
      return {
        ...state,
        errors: kept,
        activeError: calculateActiveError(kept),
      };
    }

    default:
      return state;
  }
}

// ========== Context ==========

interface ErrorContextValue {
  state: ErrorState;
  addError: (error: AppError) => void;
  dismissError: (id: string) => void;
  retryError: (id: string, action: () => Promise<void>) => void;
  clearResolvedErrors: () => void;
  createError: (
    category: ErrorCategory,
    code: string,
    message: string,
    options?: Partial<Omit<AppError, 'id' | 'category' | 'code' | 'message' | 'timestamp' | 'dismissed'>>,
  ) => string;  // 返回新错误的 ID
}

const ErrorContext = createContext<ErrorContextValue | null>(null);

export function ErrorProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(errorReducer, initialState);

  const addError = useCallback((error: AppError) => {
    dispatch({ type: 'ADD_ERROR', error });
  }, []);

  const dismissError = useCallback((id: string) => {
    dispatch({ type: 'DISMISS_ERROR', id });
  }, []);

  const retryError = useCallback((id: string, action: () => Promise<void>) => {
    dispatch({ type: 'RETRY_ERROR', id, action });
  }, []);

  const clearResolvedErrors = useCallback(() => {
    dispatch({ type: 'CLEAR_RESOLVED' });
  }, []);

  const createError = useCallback((
    category: ErrorCategory,
    code: string,
    message: string,
    options?: Partial<Omit<AppError, 'id' | 'category' | 'code' | 'message' | 'timestamp' | 'dismissed'>>,
  ): string => {
    const id = `err_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    const error: AppError = {
      id,
      category,
      code,
      message,
      detail: options?.detail,
      recoverable: options?.recoverable ?? false,
      retryAction: options?.retryAction,
      fallbackAction: options?.fallbackAction,
      timestamp: Date.now(),
      dismissed: false,
    };
    addError(error);
    return id;
  }, [addError]);

  return (
    <ErrorContext.Provider value={{ state, addError, dismissError, retryError, clearResolvedErrors, createError }}>
      {children}
    </ErrorContext.Provider>
  );
}

/** Hook：使用错误上下文 */
export function useErrorContext(): ErrorContextValue {
  const ctx = useContext(ErrorContext);
  if (!ctx) throw new Error('useErrorContext must be used within ErrorProvider');
  return ctx;
}
