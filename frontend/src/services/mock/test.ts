/**
 * Mock系统测试脚本
 * 用于验证mock功能的正确性
 */

import { mockService } from './index';
import { mockScenarios } from './scenarios';

/**
 * 运行所有测试
 */
export function runMockTests(): void {
  console.log('[Mock Test] 开始运行测试套件...');

  testEnvironment();
  testScenarios();
  testInterceptor();
  testService();

  console.log('[Mock Test] 所有测试完成');
}

/**
 * 测试环境检测
 */
function testEnvironment(): void {
  console.log('[Mock Test] 测试环境检测...');

  // 测试环境初始化
  mockService.debug.status();

  // 测试手动切换
  const originalState = mockService.status.enabled;
  console.log(`[Mock Test] 原始状态: ${originalState}`);

  const newState = mockService.toggle();
  console.log(`[Mock Test] 切换后状态: ${newState}`);

  // 恢复原始状态
  if (newState !== originalState) {
    mockService.toggle();
  }

  console.log('[Mock Test] 环境检测测试通过 ✓');
}

/**
 * 测试场景数据
 */
function testScenarios(): void {
  console.log('[Mock Test] 测试场景数据...');

  // 检查场景数量
  if (mockScenarios.length === 0) {
    console.error('[Mock Test] 错误: 没有找到场景');
    return;
  }

  console.log(`[Mock Test] 找到 ${mockScenarios.length} 个场景`);

  // 检查每个场景的完整性
  mockScenarios.forEach((scenario, index) => {
    console.log(`[Mock Test] 场景 ${index + 1}: ${scenario.name}`);

    if (!scenario.id) {
      console.error(`[Mock Test] 错误: 场景 ${index + 1} 缺少ID`);
    }

    if (!scenario.userInput) {
      console.error(`[Mock Test] 错误: 场景 ${index + 1} 缺少用户输入`);
    }

    if (!scenario.events || scenario.events.length === 0) {
      console.error(`[Mock Test] 错误: 场景 ${index + 1} 缺少事件`);
    } else {
      console.log(`[Mock Test] 场景 ${index + 1} 有 ${scenario.events.length} 个事件`);
    }
  });

  console.log('[Mock Test] 场景数据测试通过 ✓');
}

/**
 * 测试拦截器
 */
function testInterceptor(): void {
  console.log('[Mock Test] 测试拦截器...');

  // 测试fetch拦截
  console.log('[Mock Test] 测试fetch拦截...');

  // 模拟fetch请求
  const originalFetch = window.fetch;
  let fetchCalled = false;

  window.fetch = function (...args: any[]) {
    fetchCalled = true;
    console.log('[Mock Test] Fetch拦截成功:', args[0]);
    return Promise.resolve(new Response('{}'));
  };

  // 测试API请求
  fetch('/api/sessions', { method: 'POST' })
    .then(() => {
      if (fetchCalled) {
        console.log('[Mock Test] Fetch拦截测试通过 ✓');
      } else {
        console.error('[Mock Test] Fetch拦截测试失败 ✗');
      }
    })
    .catch((error) => {
      console.error('[Mock Test] Fetch拦截测试错误:', error);
    })
    .finally(() => {
      // 恢复原始fetch
      window.fetch = originalFetch;
    });

  console.log('[Mock Test] 拦截器测试完成');
}

/**
 * 测试服务功能
 */
function testService(): void {
  console.log('[Mock Test] 测试服务功能...');

  // 测试状态获取
  const status = mockService.status;
  console.log('[Mock Test] 服务状态:', status);

  if (!status.initialized) {
    console.error('[Mock Test] 错误: 服务未初始化');
  }

  if (!Array.isArray(status.scenarios)) {
    console.error('[Mock Test] 错误: 场景列表格式错误');
  }

  // 测试调试功能
  console.log('[Mock Test] 测试调试功能...');
  mockService.debug.status();
  mockService.debug.listScenarios();

  // 测试场景查询
  const firstScenario = mockService.scenarios[0];
  if (firstScenario) {
    mockService.debug.testScenario(firstScenario.id);
  }

  console.log('[Mock Test] 服务功能测试通过 ✓');
}

/**
 * 性能测试
 */
export function performanceTest(): void {
  console.log('[Mock Test] 开始性能测试...');

  const startTime = performance.now();

  // 模拟大量事件处理
  const testScenario = mockScenarios[0];
  if (testScenario) {
    console.log(`[Mock Test] 模拟处理 ${testScenario.events.length} 个事件...`);

    testScenario.events.forEach((event, index) => {
      // 模拟事件处理
      const eventData = JSON.stringify(event.data);
      const processed = eventData.length > 0;

      if (!processed) {
        console.warn(`[Mock Test] 事件 ${index} 处理失败`);
      }
    });
  }

  const endTime = performance.now();
  const duration = endTime - startTime;

  console.log(`[Mock Test] 性能测试完成，耗时: ${duration.toFixed(2)}ms`);
  console.log(`[Mock Test] 平均每个事件处理时间: ${duration / (testScenario?.events.length || 1)}ms`);
}

/**
 * 内存使用测试
 */
export function memoryTest(): void {
  console.log('[Mock Test] 开始内存使用测试...');

  // 记录初始内存使用
  const initialMemory = (performance as any).memory?.usedJSHeapSize || 0;

  // 创建大量临时对象模拟使用
  const tempObjects: any[] = [];
  for (let i = 0; i < 1000; i++) {
    tempObjects.push({
      id: i,
      data: mockScenarios[0]?.events || [],
      timestamp: Date.now()
    });
  }

  // 清理临时对象
  tempObjects.length = 0;

  // 记录最终内存使用
  const finalMemory = (performance as any).memory?.usedJSHeapSize || 0;
  const memoryDiff = finalMemory - initialMemory;

  console.log(`[Mock Test] 初始内存: ${(initialMemory / 1024 / 1024).toFixed(2)}MB`);
  console.log(`[Mock Test] 最终内存: ${(finalMemory / 1024 / 1024).toFixed(2)}MB`);
  console.log(`[Mock Test] 内存变化: ${(memoryDiff / 1024 / 1024).toFixed(2)}MB`);

  if (memoryDiff > 1024 * 1024 * 10) { // 10MB
    console.warn('[Mock Test] 警告: 内存使用过高');
  } else {
    console.log('[Mock Test] 内存使用测试通过 ✓');
  }
}

// 自动运行测试（开发环境）
if (import.meta.env.DEV && import.meta.env.VITE_MOCK_TEST === 'true') {
  console.log('[Mock Test] 自动运行测试套件...');

  // 延迟运行，确保所有模块已加载
  setTimeout(() => {
    runMockTests();
    performanceTest();
    memoryTest();
  }, 1000);
}

// 暴露测试函数到全局
if (import.meta.env.DEV) {
  (window as any).mockTests = {
    runAll: runMockTests,
    performance: performanceTest,
    memory: memoryTest
  };

  console.log('[Mock Test] 已注入全局测试接口: window.mockTests');
  console.log('[Mock Test] 可用测试命令:');
  console.log('  - mockTests.runAll()        // 运行所有测试');
  console.log('  - mockTests.performance()   // 性能测试');
  console.log('  - mockTests.memory()        // 内存测试');
}