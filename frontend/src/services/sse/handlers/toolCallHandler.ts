/**
 * Tool Call 事件处理器
 * 处理 tool_call:start / tool_call:end 事件
 */

import type { ToolCallBlock } from '../types';

// 存储活跃的 tool calls（支持并发）
const activeToolCalls = new Map<string, ToolCallBlock>();

export const toolCallHandler = {
  /**
   * 处理 tool_call:start 事件
   */
  onStart(data: {
    id: string;
    name: string;
    input?: Record<string, unknown>;
  }): ToolCallBlock {
    const toolCall: ToolCallBlock = {
      type: 'tool_call',
      id: data.id,
      name: data.name,
      input: data.input,
      status: 'running',
      startedAt: Date.now(),
    };

    activeToolCalls.set(data.id, toolCall);
    return toolCall;
  },

  /**
   * 处理 tool_call:end 事件
   */
  onEnd(data: {
    id: string;
    status: 'success' | 'error';
    durationMs?: number;
    error?: string;
  }): ToolCallBlock | null {
    const toolCall = activeToolCalls.get(data.id);
    if (!toolCall) {
      console.warn(`tool_call:end: no matching start for id ${data.id}`);
      return null;
    }

    toolCall.status = data.status;
    toolCall.endedAt = Date.now();

    if (data.durationMs ! undefined) {
      toolCall.durationMs = data.durationMs;
    } else {
      toolCall.durationMs = toolCall.endedAt - toolCall.startedAt;
    }

    if (data.error) {
      toolCall.error = data.error;
    }

    const result = { ...toolCall };
    activeToolCalls.delete(data.id); // 完成后移除
    return result;
  },

  /**
   * 获取所有活跃的 tool calls
   */
  getActive(): ToolCallBlock[] {
    return Array.from(activeToolCalls.values());
  },

  /**
   * 重置状态
   */
  reset(): void {
    activeToolCalls.clear();
  },
};
