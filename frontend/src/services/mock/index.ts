/**
 * Mock服务主入口
 * 统一管理mock系统的启动和配置
 */

import { mockEnvironment } from './environment';
import { mockInterceptor } from './interceptor';
import { mockScenarios } from './scenarios';

class MockService {
  private _initialized = false;

  /**
   * 初始化mock服务
   */
  init(): void {
    if (this._initialized) return;

    console.log('[Mock] 初始化mock服务');

    // 初始化环境检测
    mockEnvironment.init();

    // 如果启用了mock模式，启动拦截器
    if (mockEnvironment.enabled) {
      mockInterceptor.start();
    }

    // 监听环境变化
    this._setupEnvironmentWatcher();

    this._initialized = true;
  }

  /**
   * 设置环境变化监听
   */
  private _setupEnvironmentWatcher(): void {
    // 监听URL变化
    let lastUrl = location.href;
    new MutationObserver(() => {
      const currentUrl = location.href;
      if (currentUrl !== lastUrl) {
        lastUrl = currentUrl;
        this._checkEnvironmentChange();
      }
    }).observe(document, { subtree: true, childList: true });
  }

  /**
   * 检查环境变化
   */
  private _checkEnvironmentChange(): void {
    const wasEnabled = mockEnvironment.enabled;
    mockEnvironment.init();
    const isEnabled = mockEnvironment.enabled;

    if (wasEnabled !== isEnabled) {
      if (isEnabled) {
        mockInterceptor.start();
      } else {
        mockInterceptor.stop();
      }
    }
  }

  /**
   * 手动启用mock模式
   */
  enable(): void {
    mockEnvironment.enable();
    mockInterceptor.start();
  }

  /**
   * 手动禁用mock模式
   */
  disable(): void {
    mockEnvironment.disable();
    mockInterceptor.stop();
  }

  /**
   * 切换mock模式
   */
  toggle(): boolean {
    const enabled = mockEnvironment.toggle();
    if (enabled) {
      mockInterceptor.start();
    } else {
      mockInterceptor.stop();
    }
    return enabled;
  }

  /**
   * 获取当前状态
   */
  get status(): {
    enabled: boolean;
    initialized: boolean;
    scenarios: string[];
  } {
    return {
      enabled: mockEnvironment.enabled,
      initialized: this._initialized,
      scenarios: mockScenarios.map(s => s.name)
    };
  }

  /**
   * 获取所有场景
   */
  get scenarios() {
    return mockScenarios;
  }

  /**
   * 开发调试工具
   */
  debug = {
    /** 打印当前状态 */
    status: () => {
      console.log('[Mock Debug] 当前状态:', mockService.status);
    },

    /** 列出所有场景 */
    listScenarios: () => {
      console.log('[Mock Debug] 可用场景:');
      mockScenarios.forEach((scenario, index) => {
        console.log(`  ${index + 1}. ${scenario.name} (${scenario.id})`);
        console.log(`     输入: "${scenario.userInput}"`);
        console.log(`     事件数: ${scenario.events.length}`);
      });
    },

    /** 测试特定场景 */
    testScenario: (scenarioId: string) => {
      const scenario = mockScenarios.find(s => s.id === scenarioId);
      if (scenario) {
        console.log(`[Mock Debug] 测试场景: ${scenario.name}`);
        console.log('事件序列:', scenario.events.map(e => `${e.type} (${e.delay}ms)`));
      } else {
        console.warn(`[Mock Debug] 场景未找到: ${scenarioId}`);
      }
    }
  };
}

// 创建单例实例
export const mockService = new MockService();

// 自动初始化（开发环境）
if (import.meta.env.DEV) {
  // 立即初始化，不需要等待DOM
  setTimeout(() => {
    mockService.init();
  }, 0);

  // 暴露到全局，方便调试
  (window as any).mockService = mockService;

  console.log('[Mock] Mock服务已加载，等待初始化...');
  console.log('[Mock] 可用调试命令:');
  console.log('  - mockService.debug.status()        // 查看状态');
  console.log('  - mockService.debug.listScenarios() // 列出场景');
  console.log('  - mockService.debug.testScenario("react-component") // 测试场景');
  console.log('  - mockService.toggle()              // 切换mock模式');
}

export default mockService;