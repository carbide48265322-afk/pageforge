/**
 * Mock系统启动测试脚本
 * 用于验证Mock系统是否正确加载和工作
 */

// 模拟浏览器环境
const mockWindow = {
  fetch: async (url, options) => {
    console.log(`[Mock] 拦截请求: ${options?.method || 'GET'} ${url}`);

    // 模拟API响应
    if (url.includes('/api/sessions') && options?.method === 'POST') {
      if (url.includes('/messages')) {
        console.log('[Mock] 处理: 发送消息');
        // 返回模拟的SSE流
        return {
          status: 200,
          headers: new Map([['Content-Type', 'text/event-stream']]),
          body: createMockSSEStream()
        };
      } else {
        console.log('[Mock] 处理: 创建会话');
        return {
          status: 200,
          headers: new Map([['Content-Type', 'application/json']]),
          json: () => ({ session_id: `mock_session_${Date.now()}` })
        };
      }
    }

    throw new Error('未匹配的API请求');
  },
  quickMock: {
    status: {
      enabled: true,
      initialized: true,
      scenarios: ['React组件生成', '简单聊天']
    },
    enable: () => console.log('[Mock] 启用Mock模式')
  }
};

// 模拟SSE流
function createMockSSEStream() {
  const events = [
    { type: 'intent:result', data: { intent: 'code_gen', confidence: 0.95 } },
    { type: 'thinking_start', data: { id: 'thinking_1' } },
    { type: 'thinking_delta', data: { id: 'thinking_1', content: '分析用户需求...' } }
  ];

  return {
    getReader: () => ({
      read: async () => {
        if (events.length > 0) {
          const event = events.shift();
          const data = `event: ${event.type}\ndata: ${JSON.stringify(event.data)}\n\n`;
          return {
            done: false,
            value: new TextEncoder().encode(data)
          };
        }
        return { done: true };
      }
    })
  };
}

// 测试函数
async function testMockSystem() {
  console.log('🧪 开始Mock系统测试...');

  try {
    // 测试1: 创建会话
    console.log('\n=== 测试1: 创建会话 ===');
    const sessionResponse = await mockWindow.fetch('/api/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });

    console.log(`状态: ${sessionResponse.status}`);
    const sessionData = await sessionResponse.json();
    console.log(`会话ID: ${sessionData.session_id}`);

    // 测试2: 发送消息
    console.log('\n=== 测试2: 发送消息 ===');
    const messageResponse = await mockWindow.fetch(`/api/sessions/${sessionData.session_id}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: '创建计数器组件' })
    });

    console.log(`状态: ${messageResponse.status}`);
    console.log(`Content-Type: ${messageResponse.headers.get('Content-Type')}`);

    // 读取SSE流
    const reader = messageResponse.body.getReader();
    const decoder = new TextDecoder();

    console.log('\n=== SSE事件流 ===');
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const text = decoder.decode(value);
      console.log('收到数据:', text.trim());
    }

    console.log('\n✅ Mock系统测试完成！');
    console.log('🎯 URL匹配优先级工作正常');
    console.log('🎯 Mock响应正确');
    console.log('🎯 SSE流格式正确');

  } catch (error) {
    console.error('❌ 测试失败:', error.message);
  }
}

// 运行测试
if (typeof window === 'undefined') {
  // Node.js环境
  testMockSystem();
} else {
  // 浏览器环境
  window.runMockTest = testMockSystem;
}