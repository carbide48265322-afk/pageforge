/**
 * Mock系统快速修复版本
 * 确保mock能够立即工作
 */

class QuickMockFix {
  private enabled = false;
  private originalFetch: typeof fetch;

  constructor() {
    this.originalFetch = window.fetch.bind(window);
    this.init();
  }

  init() {
    console.log('[QuickMock] 初始化快速修复版Mock服务');

    // 检查URL参数
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('mock') === 'true') {
      this.enable();
    }

    // 检查环境变量
    if (import.meta.env.VITE_MOCK_MODE === 'true') {
      this.enable();
    }

    // 开发环境默认启用（如果没有明确禁用）
    if (import.meta.env.DEV && urlParams.get('mock') !== 'false') {
      console.log('[QuickMock] 开发环境检测到，默认启用Mock模式');
      this.enable();
    }

    // 暴露到全局
    (window as any).quickMock = this;
    console.log('[QuickMock] 快速修复版Mock服务已加载');
  }

  enable() {
    if (this.enabled) return;

    console.log('[QuickMock] 启用Mock模式');
    this.enabled = true;
    this.interceptFetch();
  }

  disable() {
    if (!this.enabled) return;

    console.log('[QuickMock] 禁用Mock模式');
    this.enabled = false;
    window.fetch = this.originalFetch;
  }

  private interceptFetch() {
    console.log('[QuickMock] 安装fetch拦截器');

    window.fetch = async (input, init) => {
      const url = input.toString();
      const method = init?.method || 'GET';

      // 拦截API请求
      if (url.includes('/api/')) {
        console.log('[QuickMock] 拦截API请求:', url);
        console.log('[QuickMock] 请求方法:', method);
        console.log('[QuickMock] 请求体存在:', !!init?.body);

        // 精确匹配优先级：从上到下，越精确的URL模式越在上面
        const patterns = [
          // 1. 最精确的匹配：包含session ID和/messages的URL
          {
            pattern: /\/api\/sessions\/[^/]+\/messages$/,
            method: 'POST',
            handler: () => {
              console.log('[QuickMock] 处理: 发送消息 (精确匹配)');
              const body = init.body ? JSON.parse(init.body.toString()) : {};
              const message = body.message || '';
              console.log('[QuickMock] 消息内容:', message);
              return this.createMockResponse(message);
            }
          },
          // 2. 中等精确度的匹配：只包含/sessions路径的POST请求
          {
            pattern: /\/api\/sessions$/,
            method: 'POST',
            handler: () => {
              console.log('[QuickMock] 处理: 创建会话 (中等匹配)');
              return new Response(JSON.stringify({
                session_id: `mock_session_${Date.now()}`
              }), {
                status: 200,
                headers: { 'Content-Type': 'application/json' }
              });
            }
          },
          // 3. 最宽泛的匹配：任何包含/sessions的POST请求
          {
            pattern: /\/api\/sessions/,
            method: 'POST',
            handler: () => {
              console.log('[QuickMock] 处理: 创建会话 (宽泛匹配)');
              return new Response(JSON.stringify({
                session_id: `mock_session_${Date.now()}`
              }), {
                status: 200,
                headers: { 'Content-Type': 'application/json' }
              });
            }
          }
        ];

        // 按优先级匹配模式
        for (const { pattern, method: requiredMethod, handler } of patterns) {
          if (pattern.test(url) && method === requiredMethod) {
            return handler();
          }
        }

        console.log('[QuickMock] 没有匹配到处理器，使用原始fetch');
      }

      // 其他请求使用原始fetch
      return this.originalFetch(input, init);
    };
  }

  private createMockResponse(message: string): Response {
    // 根据消息内容选择场景
    const isCounterRequest = message.includes('计数器') || message.includes('counter');

    // 创建事件序列
    const events = isCounterRequest ? this.getCounterEvents() : this.getChatEvents();

    // 创建SSE流
    const stream = this.createEventStream(events);

    return new Response(stream, {
      status: 200,
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
      }
    });
  }

  private getCounterEvents() {
    return [
      { type: 'intent:result', delay: 300, data: { intent: 'code_gen', confidence: 0.95, tags: ['react', 'component'] } },
      { type: 'thinking_start', delay: 500, data: { id: 'thinking_1' } },
      { type: 'thinking_delta', delay: 800, data: { id: 'thinking_1', content: '分析用户需求，创建计数器组件...' } },
      { type: 'thinking_end', delay: 1200, data: { id: 'thinking_1', content: '分析完成' } },
      { type: 'plan_start', delay: 1500, data: { id: 'plan_1' } },
      { type: 'plan_update', delay: 1800, data: { id: 'plan_1', steps: [{ id: 1, label: '创建Counter组件', status: 'pending' }], isComplete: false } },
      { type: 'style_selected', delay: 2100, data: { style: 'modern', primary_color: '#3b82f6' } },
      { type: 'file_created', delay: 2400, data: { file_path: '/src/Counter.tsx', name: 'Counter.tsx', language: 'typescript' } },
      { type: 'status:generation_done', delay: 3000, data: { status: 'generation_done', message: '生成完成' } },
      { type: 'text_delta', delay: 3300, data: { content: '✅ 已成功创建计数器组件！' } },
      { type: 'text_done', delay: 3600, data: {} }
    ];
  }

  private getChatEvents() {
    return [
      { type: 'intent:result', delay: 200, data: { intent: 'chat', confidence: 0.98 } },
      { type: 'text_delta', delay: 500, data: { content: '你好！我是PageForge，一个AI驱动的代码生成平台。' } },
      { type: 'text_done', delay: 800, data: {} }
    ];
  }

  private createEventStream(events: Array<{ type: string; delay: number; data: any }>): ReadableStream {
    let eventIndex = 0;
    let timeoutId: NodeJS.Timeout;

    return new ReadableStream({
      start: (controller) => {
        const sendNextEvent = () => {
          if (eventIndex >= events.length) {
            controller.close();
            return;
          }

          const event = events[eventIndex];
          timeoutId = setTimeout(() => {
            // 发送SSE事件
            const eventData = `event: ${event.type}\ndata: ${JSON.stringify(event.data)}\n\n`;
            controller.enqueue(new TextEncoder().encode(eventData));
            eventIndex++;
            sendNextEvent();
          }, event.delay);
        };

        sendNextEvent();
      },

      cancel: () => {
        if (timeoutId) {
          clearTimeout(timeoutId);
        }
      }
    });
  }

  toggle(): boolean {
    if (this.enabled) {
      this.disable();
    } else {
      this.enable();
    }
    return this.enabled;
  }

  get status() {
    return {
      enabled: this.enabled,
      initialized: true,
      scenarios: ['React组件生成', '简单聊天']
    };
  }
}

// 创建实例
const quickMockFix = new QuickMockFix();

// 导出
export default quickMockFix;