/**
 * 统一错误类型系统
 * 覆盖 PageForge 的 7 类错误场景
 */

export enum ErrorCategory {
  NETWORK = 'network',          // 网络相关（SSE 断连、API 超时）
  WEBCONTAINER = 'webcontainer', // WebContainer 相关
  DEPENDENCY = 'dependency',    // 安装依赖相关
  GENERATION = 'generation',    // LLM 代码生成相关
  FILESYSTEM = 'filesystem',    // 文件系统操作
  SERVER = 'server',            // 后端服务错误
  UNKNOWN = 'unknown',
}

/** 应用错误接口 */
export interface AppError {
  id: string;                   // 唯一标识（用于去重和跟踪）
  category: ErrorCategory;
  code: string;                 // 错误码，如 'WC_BOOT_FAILED'
  message: string;              // 用户友好的错误描述
  detail?: string;              // 技术细节（展开后显示）
  recoverable: boolean;         // 是否可恢复
  retryAction?: () => Promise<void>;  // 重试回调
  fallbackAction?: () => void;       // 降级方案回调
  timestamp: number;
  dismissed: boolean;           // 是否被用户关闭
}

/** 错误状态管理 */
export interface ErrorState {
  errors: AppError[];
  activeError: AppError | null;  // 当前最严重的未处理错误
}

// ========== 常用错误码 ==========

export const ERROR_CODES = {
  // 网络类
  SSE_DISCONNECTED: 'SSE_DISCONNECTED',
  API_TIMEOUT: 'API_TIMEOUT',

  // WebContainer 类
  WC_NOT_SUPPORTED: 'WC_NOT_SUPPORTED',
  WC_BOOT_FAILED: 'WC_BOOT_FAILED',

  // 依赖安装类
  INSTALL_TIMEOUT: 'INSTALL_TIMEOUT',
  INSTALL_FAILED: 'INSTALL_FAILED',

  // 代码生成类
  LLM_ERROR: 'LLM_ERROR',
  LLM_TOKEN_LIMIT: 'LLM_TOKEN_LIMIT',
  GENERATION_TIMEOUT: 'GENERATION_TIMEOUT',

  // 文件系统类
  FILE_WRITE_FAILED: 'FILE_WRITE_FAILED',

  // 服务端类
  SERVER_ERROR: 'SERVER_ERROR',
  INTENT_RECOGNITION_FAILED: 'INTENT_RECOGNITION_FAILED',

  // Dev Server 类
  DEV_SERVER_PORT_IN_USE: 'DEV_SERVER_PORT_IN_USE',
  DEV_SERVER_START_FAILED: 'DEV_SERVER_START_FAILED',

  // Monaco 加载失败
  MONACO_LOAD_FAILED: 'MONACO_LOAD_FAILED',
} as const;

export type ErrorCodeType = (typeof ERROR_CODES)[keyof typeof ERROR_CODES];

// ========== 重试配置 ==========

export interface RetryConfig {
  maxRetries: number;
  backoffMs: number;       // 初始退避时间 (ms)
  maxBackoffMs: number;    // 最大退避时间 (ms)
}

export const RETRY_CONFIG: Record<ErrorCategory, RetryConfig> = {
  [ErrorCategory.NETWORK]:     { maxRetries: Infinity, backoffMs: 1000, maxBackoffMs: 30000 },
  [ErrorCategory.DEPENDENCY]:  { maxRetries: 3,      backoffMs: 2000, maxBackoffMs: 10000 },
  [ErrorCategory.GENERATION]:  { maxRetries: 2,      backoffMs: 3000, maxBackoffMs: 10000 },
  [ErrorCategory.WEBCONTAINER]:{ maxRetries: 1,      backoffMs: 1000, maxBackoffMs: 5000 },
  [ErrorCategory.FILESYSTEM]:  { maxRetries: 2,      backoffMs: 1000, maxBackoffMs: 5000 },
  [ErrorCategory.SERVER]:      { maxRetries: 3,      backoffMs: 2000, maxBackoffMs: 10000 },
  [ErrorCategory.UNKNOWN]:     { maxRetries: 1,      backoffMs: 1500, maxBackoffMs: 5000 },
};

// ========== 降级方案矩阵 ==========

export type FallbackAction = () => void;

export const FALLBACK_MATRIX: Record<string, FallbackAction | null> = {
  [ERROR_CODES.WC_NOT_SUPPORTED]: null,  // 由调用方决定是否切换到 HTML iframe 模式
  [ERROR_CODES.INSTALL_FAILED]: null,   // 由调用方决定是否跳过依赖安装
  [ERROR_CODES.DEV_SERVER_PORT_IN_USE]: null,  // 由调用方自动换端口
};
