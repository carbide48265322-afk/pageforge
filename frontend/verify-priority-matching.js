/**
 * URL匹配优先级验证脚本
 * 验证修改后的mock系统是否正确处理URL匹配优先级
 */

(function() {
  console.log('🔍 URL匹配优先级验证开始...');

  // 测试URL匹配优先级
  function testUrlPriority() {
    console.log('\n=== URL匹配优先级测试 ===');

    const testCases = [
      {
        url: '/api/sessions/test-123/messages',
        method: 'POST',
        expected: '发送消息 (精确匹配)',
        description: '包含session ID和/messages的URL应该匹配发送消息'
      },
      {
        url: '/api/sessions/mock_session_1777958876434/messages',
        method: 'POST',
        expected: '发送消息 (精确匹配)',
        description: '动态session ID的/messages URL应该匹配发送消息'
      },
      {
        url: '/api/sessions',
        method: 'POST',
        expected: '创建会话 (中等匹配)',
        description: '只有/sessions路径的URL应该匹配创建会话'
      },
      {
        url: '/api/sessions/extra/path',
        method: 'POST',
        expected: '创建会话 (宽泛匹配)',
        description: '包含/sessions的其他路径应该匹配创建会话（宽泛匹配）'
      },
      {
        url: '/api/users',
        method: 'POST',
        expected: '无匹配',
        description: '不包含/sessions的URL不应该匹配任何模式'
      }
    ];

    const patterns = [
      {
        pattern: /\/api\/sessions\/[^/]+\/messages$/,
        method: 'POST',
        name: '发送消息 (精确匹配)'
      },
      {
        pattern: /\/api\/sessions$/,
        method: 'POST',
        name: '创建会话 (中等匹配)'
      },
      {
        pattern: /\/api\/sessions/,
        method: 'POST',
        name: '创建会话 (宽泛匹配)'
      }
    ];

    let passed = 0;
    let failed = 0;

    testCases.forEach((testCase, index) => {
      console.log(`\n测试 #${index + 1}: ${testCase.description}`);
      console.log(`URL: ${testCase.url}`);
      console.log(`期望: ${testCase.expected}`);

      let matched = false;
      let actualMatch = '';

      for (const { pattern, method, name } of patterns) {
        if (pattern.test(testCase.url) && testCase.method === method) {
          matched = true;
          actualMatch = name;
          break;
        }
      }

      if (!matched) {
        actualMatch = '无匹配';
      }

      console.log(`实际: ${actualMatch}`);

      if (actualMatch === testCase.expected) {
        console.log('✅ 通过');
        passed++;
      } else {
        console.log('❌ 失败');
        failed++;
      }
    });

    console.log('\n' + '='.repeat(50));
    console.log('📊 优先级测试结果');
    console.log('='.repeat(50));
    console.log(`✅ 通过: ${passed} 个测试`);
    console.log(`❌ 失败: ${failed} 个测试`);
    console.log(`📈 成功率: ${((passed / (passed + failed)) * 100).toFixed(1)}%`);

    return failed === 0;
  }

  // 测试Mock服务状态
  function testMockServices() {
    console.log('\n=== Mock服务状态检查 ===');

    const services = [
      { name: 'QuickMock', instance: window.quickMock },
      { name: 'SimpleMock', instance: window.simpleMock },
      { name: 'MockService', instance: window.mockService }
    ];

    let availableServices = 0;

    services.forEach(({ name, instance }) => {
      if (instance) {
        console.log(`✅ ${name} 已加载`);
        console.log(`   启用状态: ${instance.status?.enabled || '未知'}`);
        console.log(`   初始化状态: ${instance.status?.initialized || '未知'}`);
        availableServices++;
      } else {
        console.log(`❌ ${name} 未加载`);
      }
    });

    console.log(`\n可用Mock服务: ${availableServices}/${services.length}`);
    return availableServices > 0;
  }

  // 验证环境配置
  function testEnvironment() {
    console.log('\n=== 环境配置检查 ===');

    // 检查URL参数
    const urlParams = new URLSearchParams(window.location.search);
    const mockParam = urlParams.get('mock');
    console.log(`URL mock参数: ${mockParam || '未设置'}`);

    // 检查环境变量
    let envMock = false;
    try {
      envMock = import.meta.env.VITE_MOCK_MODE === 'true';
    } catch (e) {
      console.log('无法访问环境变量，可能是生产环境');
    }
    console.log(`环境变量MOCK_MODE: ${envMock}`);

    const shouldEnableMock = mockParam === 'true' || envMock;
    console.log(`Mock应该启用: ${shouldEnableMock}`);

    return shouldEnableMock;
  }

  // 运行所有测试
  function runAllTests() {
    console.log('🧪 开始运行URL匹配优先级验证套件...');

    const results = {
      priority: testUrlPriority(),
      services: testMockServices(),
      environment: testEnvironment()
    };

    const allPassed = Object.values(results).every(result => result);

    console.log('\n' + '='.repeat(50));
    console.log('📊 总体验证结果');
    console.log('='.repeat(50));
    console.log(`URL优先级测试: ${results.priority ? '✅ 通过' : '❌ 失败'}`);
    console.log(`Mock服务状态: ${results.services ? '✅ 通过' : '❌ 失败'}`);
    console.log(`环境配置: ${results.environment ? '✅ 通过' : '❌ 失败'}`);

    if (allPassed) {
      console.log('\n🎉 恭喜！URL匹配优先级验证通过！');
      console.log('\n🚀 现在您可以：');
      console.log('   - 在前端输入"创建计数器组件"测试完整流程');
      console.log('   - 验证/messages接口正确匹配而不是被/sessions拦截');
      console.log('   - 使用调试工具监控匹配过程');
    } else {
      console.log('\n⚠️  部分验证失败，请检查失败的项目');
      console.log('💡 建议：');
      console.log('   - 检查URL参数: ?mock=true');
      console.log('   - 检查环境变量: VITE_MOCK_MODE=true');
      console.log('   - 查看控制台详细错误信息');
    }

    return allPassed;
  }

  // 延迟运行测试，确保所有服务已加载
  setTimeout(() => {
    console.log('\n🔍 URL匹配优先级验证脚本加载完成');
    console.log('📝 可用命令:');
    console.log('   - runPriorityTests()     // 运行所有验证测试');
    console.log('   - testUrlPriority()      // 测试URL匹配优先级');
    console.log('   - testMockServices()     // 检查Mock服务状态');
    console.log('   - testEnvironment()      // 检查环境配置');

    // 暴露到全局
    window.runPriorityTests = runAllTests;
    window.testUrlPriority = testUrlPriority;
    window.testMockServices = testMockServices;
    window.testEnvironment = testEnvironment;

    console.log('\n⏳ 5秒后自动运行验证...');
    setTimeout(runAllTests, 5000);
  }, 1000);
})();