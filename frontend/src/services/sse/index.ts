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

// 工具函数导出
export { parseSSELine, parseSSEMessage } from './utils/parseEvent';
