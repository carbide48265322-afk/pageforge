/**
 * SSE 事件分发器
 * 三层架构的核心：连接管理 + 事件路由
 *
 * 设计：后端统一用 event: message，细分类型在 data.type 中。
 * 前端只需监听一个 message 事件，通过 data.type 分发到对应 handler。
 *
 * 支持两种模式：
 * 1. GET 模式（EventSource）：监听 message 事件，从 data.type 分发
 * 2. POST 模式（fetch + 流读取）：解析 SSE 行，从 data.type 分发
 */

import { parseSSELine, parseSSEMessage } from './utils/parseEvent';

export class SseEventDispatcher {
  private eventSource: EventSource | null = null;
  private listeners = new Map<string, Set<(data: unknown) => void>>();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private url: string;
  private activeAbortControllers: AbortController[] = [];

  constructor(url: string) {
    this.url = url;
  }

  /**
   * 订阅某类事件的数据变化（按 data.type 过滤）
   * @returns 取消订阅函数
   */
  on(eventType: string, callback: (data: unknown) => void): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(callback);

    return () => {
      const listeners = this.listeners.get(eventType);
      if (listeners) {
        listeners.delete(callback);
        if (listeners.size === 0) {
          this.listeners.delete(eventType);
        }
      }
    };
  }

  /**
   * 建立 GET SSE 连接（仅监听事件）
   * 统一监听 message 事件，从 data.type 分发
   */
  connect(): void {
    if (this.eventSource) {
      this.disconnect();
    }

    this.eventSource = new EventSource(this.url);

    // 统一监听 message 事件，从 data.type 分发
    this.eventSource.addEventListener('message', (event) => {
      try {
        const data = JSON.parse(event.data);
        const eventType = data?.type as string;
        if (eventType) {
          this.handleSSEEvent(eventType, data);
        }
      } catch {
        // 忽略 JSON 解析错误
      }
    });

    this.eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      this.handleReconnect();
    };

    this.eventSource.onopen = () => {
      console.log('SSE connection established');
      this.reconnectAttempts = 0;
    };
  }

  /**
   * 发送消息并接收 SSE 流（POST 模式）
   * 解析 SSE 行，从 data.type 分发
   * @returns AbortController 可用于取消请求
   */
  sendMessage(message: string): AbortController {
    const controller = new AbortController();
    this.activeAbortControllers.push(controller);

    fetch(this.url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
      signal: controller.signal,
    })
      .then(async (res) => {
        if (!res.ok || !res.body) {
          throw new Error(`Stream failed: ${res.status}`);
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          let currentEvent = '';
          for (const line of lines) {
            if (line.startsWith('event:')) {
              currentEvent = line.slice(7).trim();
            } else if (line.startsWith('data:')) {
              const dataStr = line.slice(5).trim();
              try {
                const data = JSON.parse(dataStr);
                // 统一从 data.type 获取事件类型
                if (currentEvent === 'message') {
                  const eventType = data?.type as string;
                  if (eventType) {
                    this.handleSSEEvent(eventType, data);
                  }
                } else {
                  // 旧格式兼容：直接用 SSE event 字段
                  if (currentEvent) {
                    this.handleSSEEvent(currentEvent, data);
                  }
                }
              } catch {
                // 忽略 JSON 解析错误
              }
              currentEvent = '';
            }
          }
        }
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          console.error('SSE POST error:', err);
          this.handleSSEEvent('error', { message: err.message });
        }
      })
      .finally(() => {
        const index = this.activeAbortControllers.indexOf(controller);
        if (index > -1) {
          this.activeAbortControllers.splice(index, 1);
        }
      });

    return controller;
  }

  /**
   * 关闭所有连接
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }

    this.activeAbortControllers.forEach(controller => {
      try { controller.abort(); } catch {}
    });
    this.activeAbortControllers = [];
  }

  /**
   * 处理 SSE 事件：通知所有订阅者
   */
  private handleSSEEvent(eventName: string, data: unknown): void {
    const subscribers = this.listeners.get(eventName);
    if (subscribers) {
      subscribers.forEach(cb => {
        try {
          cb(data);
        } catch (err) {
          console.error(`Subscriber error for event ${eventName}:`, err);
        }
      });
    }
  }

  /**
   * 重连逻辑（指数退避）
   */
  private handleReconnect(): void {
    this.disconnect();

    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error(`Max reconnection attempts (${this.maxReconnectAttempts}) reached`);
      return;
    }

    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * 获取当前连接状态
   */
  get readyState(): number {
    return this.eventSource?.readyState ?? EventSource.CLOSED;
  }
}
