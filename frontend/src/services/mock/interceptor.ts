/**
 * API拦截器
 * 将API请求重定向到mock数据
 */

import { mockEnvironment } from './environment';
import { mockScenarios } from './scenarios';
import type { MockScenario, MockEvent } from './scenarios';

class MockInterceptor {
  private _originalFetch: typeof fetch;
  private _originalEventSource: typeof EventSource;

  constructor() {
    this._originalFetch = window.fetch;
    this._originalEventSource = window.EventSource;
  }

  /**
   * 启动拦截器
   */
  start(): void {
    if (!mockEnvironment.enabled) return;

    console.log('[Mock] 启动API拦截器');

    // 拦截fetch请求
    this._interceptFetch();

    // 拦截EventSource (SSE)
    this._interceptEventSource();
  }

  /**
   * 停止拦截器
   */
  stop(): void {
    console.log('[Mock] 停止API拦截器');

    // 恢复原始fetch
    if (this._originalFetch) {
      window.fetch = this._originalFetch;
    }

    // 恢复原始EventSource
    if (this._originalEventSource) {
      window.EventSource = this._originalEventSource;
    }
  }

  /**
   * 拦截fetch请求
   */
  private _interceptFetch(): void {
    const self = this;
    window.fetch = new Proxy(this._originalFetch, {
      apply: async function (target, thisArg, args) {
        const [url, options] = args;
        const urlString = url.toString();

        // 只拦截API请求
        if (urlString.includes('/api/')) {
          return await self._handleFetchRequest(urlString, options);
        }

        // 其他请求正常处理
        return await target.apply(thisArg, args);
      }
    });
  }

  /**
   * 处理fetch请求
   */
  private async _handleFetchRequest(url: string, options?: RequestInit): Promise<Response> {
    const method = options?.method || 'GET';

    console.log(`[Mock] 拦截${method}请求:`, url);
    console.log(`[Mock] 请求详情:`, {
      url,
      method,
      hasBody: !!options?.body,
      contentType: options?.headers?.['Content-Type'] || options?.headers?.['content-type']
    });

    // 精确匹配优先级：从上到下，越精确的URL模式越在上面
    const patterns = [
      // 1. 最精确的匹配：包含session ID和具体操作的URL
      {
        pattern: /\/api\/sessions\/[^/]+\/messages$/,
        method: 'POST',
        handler: () => {
          console.log('[Mock] 匹配到: 发送消息 (精确匹配)');
          const body = options?.body ? JSON.parse(options.body.toString()) : {};
          console.log('[Mock] 消息内容:', body.message);
          return this._mockSendMessage(body.message);
        }
      },
      {
        pattern: /\/api\/sessions\/[^/]+\/versions$/,
        method: 'GET',
        handler: () => {
          console.log('[Mock] 匹配到: 获取版本列表 (精确匹配)');
          return this._mockGetVersions();
        }
      },
      {
        pattern: /\/api\/sessions\/[^/]+\/html$/,
        method: 'GET',
        handler: () => {
          console.log('[Mock] 匹配到: 获取HTML内容 (精确匹配)');
          return this._mockGetHtml();
        }
      },
      // 2. 中等精确度的匹配：只包含/sessions路径
      {
        pattern: /\/api\/sessions$/,
        method: 'POST',
        handler: () => {
          console.log('[Mock] 匹配到: 创建会话 (中等匹配)');
          return this._mockCreateSession();
        }
      },
      // 3. 最宽泛的匹配：任何包含/sessions的POST请求
      {
        pattern: /\/api\/sessions/,
        method: 'POST',
        handler: () => {
          console.log('[Mock] 匹配到: 创建会话 (宽泛匹配)');
          return this._mockCreateSession();
        }
      }
    ];

    // 按优先级匹配模式
    for (const { pattern, method: requiredMethod, handler } of patterns) {
      if (pattern.test(url) && method === requiredMethod) {
        return handler();
      }
    }

    console.log('[Mock] 没有匹配到任何处理器，返回404');
    // 默认返回404
    return new Response(JSON.stringify({ error: 'Mock endpoint not found' }), {
      status: 404,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  /**
   * 拦截EventSource (SSE)
   */
  private _interceptEventSource(): void {
    const self = this;
    const OriginalEventSource = this._originalEventSource;

    window.EventSource = function (url: string, options?: EventSourceInit) {
      // 只拦截SSE API请求
      if (url.includes('/api/sessions/') && url.includes('/messages')) {
        console.log('[Mock] 拦截SSE连接:', url);
        return new MockEventSource(url, options);
      }

      // 其他SSE连接正常处理
      return new OriginalEventSource(url, options);
    } as any;
  }

  /**
   * Mock创建会话
   */
  private _mockCreateSession(): Response {
    const sessionId = `mock_session_${Date.now()}`;
    return new Response(JSON.stringify({ session_id: sessionId }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  /**
   * Mock发送消息
   */
  private _mockSendMessage(message: string): Response {
    // 根据消息内容选择合适的场景
    let scenario = mockScenarios[0]; // 默认使用第一个场景

    if (message.includes('计数器') || message.includes('counter')) {
      scenario = mockScenarios.find(s => s.id === 'react-component') || scenario;
    } else if (message.includes('你好') || message.includes('帮助')) {
      scenario = mockScenarios.find(s => s.id === 'simple-chat') || scenario;
    }

    // 返回SSE流响应
    const stream = this._createMockSSEStream(scenario);
    return new Response(stream, {
      status: 200,
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
      }
    });
  }

  /**
   * 创建Mock SSE流
   */
  private _createMockSSEStream(scenario: MockScenario): ReadableStream {
    let eventIndex = 0;
    let timeoutId: NodeJS.Timeout | null = null;

    const sendNextEvent = (
      controller: ReadableStreamDefaultController,
      events: MockEvent[],
      index: number
    ): void => {
      if (index >= events.length) {
        // 所有事件发送完毕，关闭流
        controller.close();
        return;
      }

      const event = events[index];

      // 设置延迟
      timeoutId = setTimeout(() => {
        // 发送SSE事件
        const eventData = `event: ${event.type}\ndata: ${JSON.stringify(event.data)}\n\n`;
        controller.enqueue(new TextEncoder().encode(eventData));

        // 发送下一个事件
        sendNextEvent(controller, events, index + 1);
      }, event.delay);
    };

    return new ReadableStream({
      start: (controller) => {
        // 开始发送事件
        sendNextEvent(controller, scenario.events, eventIndex);
      },

      cancel: () => {
        if (timeoutId) {
          clearTimeout(timeoutId);
        }
      }
    });
  }

  /**
   * Mock获取版本列表
   */
  private _mockGetVersions(): Response {
    const versions = [
      {
        version: 1,
        session_id: 'mock_session',
        timestamp: new Date().toISOString(),
        summary: '初始版本',
        parent_version: null,
        trigger_message: '创建计数器组件',
        type: 'project'
      }
    ];

    return new Response(JSON.stringify({
      versions,
      current_base: 1
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  /**
   * Mock获取HTML/项目内容
   */
  private _mockGetHtml(): Response {
    const mockProject = {
      type: 'project',
      project_id: 'mock_project_1',
      files: [
        {
          path: '/src/Counter.tsx',
          content: `import React, { useState } from 'react';

export default function Counter() {
  const [count, setCount] = useState(0);

  const increment = () => setCount(count + 1);
  const decrement = () => setCount(count - 1);
  const reset = () => setCount(0);

  return (
    <div className="counter">
      <h1>计数器</h1>
      <div className="count">{count}</div>
      <div className="buttons">
        <button onClick={decrement}>-</button>
        <button onClick={reset}>重置</button>
        <button onClick={increment}>+</button>
      </div>
    </div>
  );
}`,
          size: 1024,
          modified: Date.now(),
          is_binary: false
        }
      ],
      preview_url: 'http://localhost:6001',
      version: 1
    };

    return new Response(JSON.stringify(mockProject), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

/**
 * Mock EventSource实现
 */
class MockEventSource {
  private _url: string;
  private _options?: EventSourceInit;
  private _readyState: number = 0; // CONNECTING
  private _onopen?: ((event: Event) => void);
  private _onmessage?: ((event: MessageEvent) => void);
  private _onerror?: ((event: Event) => void);

  constructor(url: string, options?: EventSourceInit) {
    this._url = url;
    this._options = options;

    // 模拟连接延迟
    setTimeout(() => {
      this._readyState = 1; // OPEN
      if (this._onopen) {
        this._onopen(new Event('open'));
      }
    }, 100);
  }

  get url(): string { return this._url; }
  get readyState(): number { return this._readyState; }
  get onopen(): ((event: Event) => void) | undefined { return this._onopen; }
  set onopen(handler: ((event: Event) => void) | undefined) { this._onopen = handler; }
  get onmessage(): ((event: MessageEvent) => void) | undefined { return this._onmessage; }
  set onmessage(handler: ((event: MessageEvent) => void) | undefined) { this._onmessage = handler; }
  get onerror(): ((event: Event) => void) | undefined { return this._onerror; }
  set onerror(handler: ((event: Event) => void) | undefined) { this._onerror = handler; }

  close(): void {
    this._readyState = 2; // CLOSED
  }
}

export const mockInterceptor = new MockInterceptor();