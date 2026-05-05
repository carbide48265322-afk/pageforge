/**
 * Mock环境检测
 * 自动检测是否启用mock模式
 */

class MockEnvironment {
  private _enabled: boolean = false;
  private _initialized: boolean = false;

  /**
   * 初始化环境检测
   */
  init(): void {
    if (this._initialized) return;

    // 1. 检查URL参数
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('mock') === 'true') {
      this._enabled = true;
      console.log('[Mock] 通过URL参数启用mock模式');
      this._initialized = true;
      return;
    }

    // 2. 检查环境变量
    if (import.meta.env.VITE_MOCK_MODE === 'true') {
      this._enabled = true;
      console.log('[Mock] 通过环境变量启用mock模式');
      this._initialized = true;
      return;
    }

    // 3. 开发环境自动检测
    if (import.meta.env.DEV) {
      // 检查后端是否可用
      this._checkBackendHealth().then(isAvailable => {
        if (!isAvailable) {
          this._enabled = true;
          console.log('[Mock] 检测到后端不可用，自动启用mock模式');
        }
        this._initialized = true;
      });
    } else {
      this._initialized = true;
    }
  }

  /**
   * 检查后端健康状态
   */
  private async _checkBackendHealth(): Promise<boolean> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);

      const response = await fetch('http://localhost:9000/api/health', {
        signal: controller.signal,
        headers: {
          'Cache-Control': 'no-cache'
        }
      });

      clearTimeout(timeoutId);
      return response.ok;
    } catch (error) {
      console.warn('[Mock] 后端健康检查失败:', error);
      return false;
    }
  }

  /**
   * 是否启用mock模式
   */
  get enabled(): boolean {
    if (!this._initialized) {
      this.init();
    }
    return this._enabled;
  }

  /**
   * 手动启用mock模式
   */
  enable(): void {
    this._enabled = true;
    console.log('[Mock] 手动启用mock模式');
  }

  /**
   * 手动禁用mock模式
   */
  disable(): void {
    this._enabled = false;
    console.log('[Mock] 手动禁用mock模式');
  }

  /**
   * 切换mock模式
   */
  toggle(): boolean {
    this._enabled = !this._enabled;
    console.log(`[Mock] ${this._enabled ? '启用' : '禁用'}mock模式`);
    return this._enabled;
  }
}

export const mockEnvironment = new MockEnvironment();