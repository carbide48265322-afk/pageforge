/**
 * SSE 事件解析工具
 * 将 SSE 原始文本解析为结构化对象
 */

import type { SSEEvent } from '../types';

/**
 * 解析 SSE 单行/单事件数据
 * SSE 格式示例：
 * event: thinking_start
 * data: {"id":"123","content":"..."}
 *
 * @param raw - SSE 原始数据字符串
 * @returns 解析后的事件对象，解析失败返回 null
 */
export function parseSSELine(raw: string): SSEEvent | null {
  try {
    // SSE 数据可能包含多个字段，格式为：
    // event: <event_name>\ndata: <json_data>\n\n
    const lines = raw.trim().split('\n');

    let eventName = '';
    let dataStr = '';

    for (const line of lines) {
      if (line.startsWith('event:')) {
        eventName = line.substring(6).trim();
      } else if (line.startsWith('data:')) {
        dataStr = line.substring(5).trim();
      }
    }

    if (!eventName || !dataStr) {
      console.warn('Invalid SSE format, missing event or data:', raw);
      return null;
    }

    // 解析 data JSON
    let data: unknown;
    try {
      data = JSON.parse(dataStr);
    } catch {
      // 如果不是 JSON，直接返回字符串
      data = dataStr;
    }

    return {
      event: eventName,
      data,
    };
  } catch (err) {
    console.error('Failed to parse SSE event:', err, 'Raw:', raw);
    return null;
  }
}

/**
 * 解析完整的 SSE 消息（可能包含多个事件）
 * @param raw - 原始 SSE 文本
 * @returns 事件对象数组
 */
export function parseSSEMessage(raw: string): SSEEvent[] {
  const events: SSEEvent[] = [];
  // SSE 消息以 \n\n 分隔
  const parts = raw.split('\n\n');

  for (const part of parts) {
    if (part.trim()) {
      const event = parseSSELine(part);
      if (event) {
        events.push(event);
      }
    }
  }

  return events;
}
