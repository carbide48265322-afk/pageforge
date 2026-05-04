/**
 * Intent 事件处理器
 * 处理 intent:* 系列事件
 */

import type { IntentResult } from '../types';

// 当前意图识别结果
let currentIntent: IntentResult | null = null;

export const intentHandler = {
  /**
   * 处理 intent:start 事件
   */
  onStart(_data: Record<string, unknown>): null {
    // intent:start 不做特殊处理，只通知订阅者
    return null;
  },

  /**
   * 处理 intent:result 事件
   */
  onResult(data: {
    intent: IntentResult['intent'];
    confidence: number;
    tags?: string[];
    mode?: IntentResult['mode'];
    complexity?: IntentResult['complexity'];
    suggested_style?: string;
  }): IntentResult {
    currentIntent = {
      intent: data.intent,
      confidence: data.confidence,
      tags: data.tags || [],
      mode: data.mode || null,
      complexity: data.complexity || null,
      suggested_style: data.suggested_style,
    };
    return currentIntent;
  },

  /**
   * 处理 intent:style_query 事件
   */
  onStyleQuery(data: {
    options: string[];
    auto_select?: string;
    timeout_ms?: number;
  }): Record<string, unknown> {
    // 返回给订阅者，供 UI 显示风格选择对话框
    return data;
  },

  /**
   * 处理 intent:style_selected 事件
   */
  onStyleSelected(data: { style: string }): Record<string, unknown> {
    if (currentIntent) {
      currentIntent.suggested_style = data.style;
    }
    return data;
  },

  /**
   * 获取当前意图识别结果
   */
  getCurrent(): IntentResult | null {
    return currentIntent;
  },

  /**
   * 重置状态
   */
  reset(): void {
    currentIntent = null;
  },
};
