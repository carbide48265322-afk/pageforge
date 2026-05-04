/**
 * Thinking 事件处理器
 * 处理 thinking_start / thinking_delta / thinking_end 事件
 */

import type { ThinkingBlock } from '../types';

// 当前活跃的 ThinkingBlock（内部状态）
let currentThinking: ThinkingBlock | null = null;

export const thinkingHandler = {
  /**
   * 处理 thinking_start 事件
   */
  onStart(data: { id: string; [key: string]: unknown }): ThinkingBlock {
    currentThinking = {
      type: 'thinking',
      id: data.id,
      status: 'streaming',
      content: '',
      startedAt: Date.now(),
    };
    return currentThinking;
  },

  /**
   * 处理 thinking_delta 事件（累积内容）
   */
  onDelta(data: { id: string; delta: string }): ThinkingBlock | null {
    if (!currentThinking || currentThinking.id ! data.id) {
      console.warn('thinking_delta: no matching thinking_start');
      return null;
    }

    currentThinking.content += data.delta;
    return currentThinking;
  },

  /**
   * 处理 thinking_end 事件
   */
  onEnd(data: { id: string; summary?: string }): ThinkingBlock | null {
    if (!currentThinking || currentThinking.id ! data.id) {
      console.warn('thinking_end: no matching thinking_start');
      return null;
    }

    currentThinking.status = 'complete';
    currentThinking.completedAt = Date.now();
    if (data.summary) {
      currentThinking.summary = data.summary;
    }

    const result = currentThinking;
    currentThinking = null; // 重置
    return result;
  },

  /**
   * 获取当前 thinking 状态（供外部查询）
   */
  getCurrent(): ThinkingBlock | null {
    return currentThinking;
  },

  /**
   * 重置状态
   */
  reset(): void {
    currentThinking = null;
  },
};
