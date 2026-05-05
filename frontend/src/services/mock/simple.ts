/**
 * 简化版Mock服务
 * 专注于解决mock不生效的问题
 */

class SimpleMockService {
  private enabled = false;
  private originalFetch: typeof fetch;

  constructor() {
    this.originalFetch = window.fetch.bind(window);
    this.init();
  }

  init() {
    console.log('[SimpleMock] 初始化简化版Mock服务');

    // 检查URL参数
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('mock') === 'true') {
      this.enable();
    }

    // 检查环境变量
    if (import.meta.env.VITE_MOCK_MODE === 'true') {
      this.enable();
    }
  }

  enable() {
    if (this.enabled) return;

    console.log('[SimpleMock] 启用Mock模式');
    this.enabled = true;
    this.interceptFetch();
  }

  disable() {
    if (!this.enabled) return;

    console.log('[SimpleMock] 禁用Mock模式');
    this.enabled = false;
    this.restoreFetch();
  }

  private interceptFetch() {
    console.log('[SimpleMock] 开始拦截fetch请求');

    window.fetch = async (input, init) => {
      const url = input.toString();

      // 只拦截API请求
      if (url.includes('/api/')) {
        console.log('[SimpleMock] 拦截API请求:', url);

        // 模拟创建会话
        if (url.includes('/api/sessions') && init?.method === 'POST') {
          return new Response(JSON.stringify({
            session_id: `mock_session_${Date.now()}`
          }), {
            status: 200,
            headers: { 'Content-Type': 'application/json' }
          });
        }

        // 模拟发送消息
        if (url.includes('/api/sessions/') && url.includes('/messages') && init?.method === 'POST') {
          const body = init.body ? JSON.parse(init.body.toString()) : {};
          const message = body.message || '';

          console.log('[SimpleMock] 模拟发送消息:', message);

          // 根据消息内容返回不同的SSE流
          if (message.includes('计数器') || message.includes('counter')) {
            return this.createCounterSSEStream();
          } else {
            return this.createChatSSEStream();
          }
        }
      }

      // 其他请求使用原始fetch
      return this.originalFetch(input, init);
    };
  }

  private restoreFetch() {
    window.fetch = this.originalFetch;
  }

  private createCounterSSEStream(): Response {
    const events = [
      { type: 'intent:result', delay: 300, data: { intent: 'code_gen', confidence: 0.95 } },
      { type: 'thinking_start', delay: 500, data: { id: 'thinking_1' } },
      { type: 'thinking_delta', delay: 800, data: { id: 'thinking_1', content: '分析用户需求...' } },
      { type: 'thinking_end', delay: 1200, data: { id: 'thinking_1', content: '分析完成' } },
      { type: 'plan_start', delay: 1500, data: { id: 'plan_1' } },
      { type: 'plan_update', delay: 1800, data: { id: 'plan_1', steps: [{ id: 1, label: '创建组件', status: 'pending' }], isComplete: false } },
      { type: 'style_selected', delay: 2100, data: { style: 'modern', primary_color: '#3b82f6' } },
      { type: 'file_created', delay: 2400, data: { file_path: '/src/Counter.tsx', name: 'Counter.tsx', language: 'typescript' } },
      { type: 'status:generation_done', delay: 3000, data: { status: 'generation_done', message: '生成完成' } },
      { type: 'text_delta', delay: 3300, data: { content: '✅ 已成功创建计数器组件！' } },
      { type: 'text_done', delay: 3600, data: {} }
    ];

    const stream = this.createSSEStream(events);
    return new Response(stream, {
      status: 200,
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
      }
    });
  }

  private createChatSSEStream(): Response {
    const events = [
      { type: 'intent:result', delay: 200, data: { intent: 'chat', confidence: 0.98 } },
      { type: 'text_delta', delay: 500, data: { content: '你好！我是PageForge，一个AI驱动的代码生成平台。' } },
      { type: 'text_done', delay: 800, data: {} }
    ];

    const stream = this.createSSEStream(events);
    return new Response(stream, {
      status: 200,
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
      }
    });
  }

  private createSSEStream(events: Array<{ type: string; delay: number; data: any }>): ReadableStream {
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
            // 使用正确的SSE格式：event: event_name\ndata: json_data\n\n
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

// 创建全局实例
const simpleMockService = new SimpleMockService();
(window as any).simpleMock = simpleMockService;

console.log('[SimpleMock] 简化版Mock服务已加载');
console.log('[SimpleMock] 可用命令:');
console.log('  - simpleMock.enable()    // 启用mock');
console.log('  - simpleMock.disable()   // 禁用mock');
console.log('  - simpleMock.toggle()    // 切换mock');
console.log('  - simpleMock.status      // 查看状态');

export default simpleMockService;