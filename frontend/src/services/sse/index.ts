/**
 * SSE 事件分发器 - 统一导出
 */

export { SseEventDispatcher } from './SseEventDispatcher';
export type { SSEEvent } from './types';

// 类型导出
export type {
  ThinkingBlock,
  PlanBlock,
  PlanStep,
  ToolCallBlock,
  FileNode,
  WebContainerPhase,
  StatusEvent,
  IntentResult,
  StyleConfig,
  RenderBlock,
  SSEStatus,
  PreviewSource,
} from './types';

// Handler 导出（供高级用法）
export { thinkingHandler } from './handlers/thinkingHandler';
export { planHandler } from './handlers/planHandler';
export { toolCallHandler } from './handlers/toolCallHandler';
export { fileEventHandler } from './handlers/fileEventHandler';
export { statusHandler } from './handlers/statusHandler';
export { intentHandler } from './handlers/intentHandler';
export { styleHandler } from './handlers/styleHandler';

// 工具函数导出
export { parseSSELine, parseSSEMessage } from './utils/parseEvent';
