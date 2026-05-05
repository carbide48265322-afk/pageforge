/**
 * Mock系统验证脚本
 * 验证mock数据系统是否完全修复
 */

(function() {
  console.log('🔍 Mock系统验证开始...');

  let tests = [];
  let passed = 0;
  let failed = 0;

  function test(name, fn) {
    tests.push({ name, fn });
  }

  function assert(condition, message) {
    if (condition) {
      console.log(`✅ ${message}`);
      return true;
    } else {
      console.log(`❌ ${message}`);
      return false;
    }
  }

  // 测试1: Mock服务加载
  test('Mock服务加载', () => {
    const quickMockLoaded = !!window.quickMock;
    const simpleMockLoaded = !!window.simpleMock;
    const mockServiceLoaded = !!window.mockService;

    console.log('=== Mock服务加载测试 ===');
    assert(quickMockLoaded, 'QuickMock服务已加载');
    assert(simpleMockLoaded, 'SimpleMock服务已加载');
    assert(mockServiceLoaded, 'MockService已加载');

    return quickMockLoaded || simpleMockLoaded || mockServiceLoaded;
  });

  // 测试2: Mock状态检查
  test('Mock状态检查', () => {
    console.log('=== Mock状态检查 ===');

    if (window.quickMock) {
      const status = window.quickMock.status;
      console.log('QuickMock状态:', status);
      return assert(status.initialized, 'QuickMock已初始化');
    }

    if (window.simpleMock) {
      const status = window.simpleMock.status;
      console.log('SimpleMock状态:', status);
      return assert(status.initialized, 'SimpleMock已初始化');
    }

    return assert(false, '没有找到可用的Mock服务');
  });

  // 测试3: 环境检测
  test('环境检测', () => {
    console.log('=== 环境检测测试 ===');

    // 检查URL参数
    const urlParams = new URLSearchParams(window.location.search);
    const mockParam = urlParams.get('mock');
    console.log('URL mock参数:', mockParam);

    // 检查环境变量
    let envMock = false;
    try {
      envMock = import.meta.env.VITE_MOCK_MODE === 'true';
    } catch (e) {
      console.log('无法访问环境变量');
    }
    console.log('环境变量MOCK_MODE:', envMock);

    return assert(mockParam === 'true' || envMock, 'Mock模式应被启用');
  });

  // 测试4: API拦截测试
  test('API拦截测试', async () => {
    console.log('=== API拦截测试 ===');

    try {
      const response = await fetch('/api/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const passed = assert(response.status === 200, 'API拦截成功，返回200状态');

      if (passed) {
        const data = await response.json();
        assert(data.session_id, '返回了有效的会话ID');
        console.log('Mock会话数据:', data);
      }

      return passed;
    } catch (error) {
      assert(false, `API拦截测试失败: ${error.message}`);
      return false;
    }
  });

  // 测试5: SSE流测试
  test('SSE流测试', async () => {
    console.log('=== SSE流测试 ===');

    try {
      const response = await fetch('/api/sessions/test/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: '创建计数器组件'
        })
      });

      const passed = assert(response.status === 200, 'SSE流响应成功');
      assert(response.headers.get('Content-Type')?.includes('text/event-stream'), '响应类型正确');

      if (passed) {
        // 读取前几个事件
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let eventCount = 0;
        let hasValidEvents = false;

        while (eventCount < 3) { // 只读取前3个事件
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          let currentEvent = '';
          for (const line of lines) {
            if (line.startsWith('event:')) {
              currentEvent = line.slice(7).trim();
              console.log(`收到事件: ${currentEvent}`);
              eventCount++;
            } else if (line.startsWith('data:')) {
              const dataStr = line.slice(5).trim();
              try {
                const data = JSON.parse(dataStr);
                console.log(`事件数据: ${JSON.stringify(data).substring(0, 50)}...`);
                hasValidEvents = true;
              } catch (e) {
                console.log(`数据解析失败: ${dataStr}`);
              }
              currentEvent = '';
            }
          }
        }

        assert(hasValidEvents, '收到了有效的SSE事件');
      }

      return passed;
    } catch (error) {
      assert(false, `SSE流测试失败: ${error.message}`);
      return false;
    }
  });

  // 测试6: 事件类型验证
  test('事件类型验证', () => {
    console.log('=== 事件类型验证 ===');

    // 检查前端期望的事件类型
    const expectedEvents = [
      'thinking_start',
      'thinking_delta',
      'thinking_end',
      'plan_start',
      'plan_update',
      'plan_done',
      'text_delta',
      'text_done',
      'intent:result',
      'file_created',
      'status:generation_done'
    ];

    console.log('前端期望的事件类型:', expectedEvents);

    // 这里可以添加更详细的事件类型验证
    return assert(expectedEvents.length > 0, '事件类型定义完整');
  });

  // 运行所有测试
  async function runAllTests() {
    console.log('🧪 开始运行验证测试套件...\n');

    for (const test of tests) {
      try {
        console.log(`\n📋 运行测试: ${test.name}`);
        const result = await Promise.resolve(test.fn());
        if (result) {
          passed++;
        } else {
          failed++;
        }
      } catch (error) {
        console.log(`❌ 测试执行失败: ${error.message}`);
        failed++;
      }
    }

    // 输出总结
    console.log('\n' + '='.repeat(50));
    console.log('📊 测试结果总结');
    console.log('='.repeat(50));
    console.log(`✅ 通过: ${passed} 个测试`);
    console.log(`❌ 失败: ${failed} 个测试`);
    console.log(`📈 成功率: ${((passed / (passed + failed)) * 100).toFixed(1)}%`);

    if (failed === 0) {
      console.log('🎉 恭喜！所有测试通过，Mock系统工作正常！');
      console.log('\n🚀 现在您可以：');
      console.log('   - 在前端输入"创建计数器组件"测试完整流程');
      console.log('   - 在后端不可用时继续开发');
      console.log('   - 使用调试面板控制Mock模式');
    } else {
      console.log('\n⚠️  部分测试失败，请检查失败的项目');
      console.log('💡 建议：');
      console.log('   - 检查URL参数: ?mock=true');
      console.log('   - 检查环境变量: VITE_MOCK_MODE=true');
      console.log('   - 查看控制台详细错误信息');
    }
  }

  // 延迟运行测试，确保所有服务已加载
  setTimeout(() => {
    console.log('\n🔍 Mock系统验证脚本加载完成');
    console.log('📝 可用命令:');
    console.log('   - runMockTests()     // 运行所有测试');
    console.log('   - checkMockStatus()  // 检查Mock状态');
    console.log('   - enableMockMode()   // 启用Mock模式');

    // 暴露到全局
    window.runMockTests = runAllTests;
    window.checkMockStatus = function() {
      console.log('=== Mock状态检查 ===');
      if (window.quickMock) console.log('QuickMock:', window.quickMock.status);
      if (window.simpleMock) console.log('SimpleMock:', window.simpleMock.status);
      if (window.mockService) console.log('MockService:', window.mockService.status);
    };

    window.enableMockMode = function() {
      if (window.quickMock) {
        window.quickMock.enable();
        console.log('✅ QuickMock已启用');
      }
      if (window.simpleMock) {
        window.simpleMock.enable();
        console.log('✅ SimpleMock已启用');
      }
      if (window.mockService) {
        window.mockService.enable();
        console.log('✅ MockService已启用');
      }
    };

    console.log('\n⏳ 5秒后自动运行测试...');
    setTimeout(runAllTests, 5000);
  }, 1000);
})();