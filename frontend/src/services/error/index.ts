/**
 * Error Service - 统一导出
 */

// 类型
export {
  ErrorCategory,
  type AppError,
  type ErrorState,
  ERROR_CODES,
  type ErrorCodeType,
  RETRY_CONFIG,
  FALLBACK_MATRIX,
} from './types';

// 重试工具
export { retryWithBackoff } from './retry';

// 状态管理
export { ErrorProvider, useErrorContext } from './ErrorStore';

// UI 组件
export { ErrorToast, ErrorToastContainer } from './ErrorToast';
export { ErrorCard, GlobalErrorBoundary } from './ErrorCard';
