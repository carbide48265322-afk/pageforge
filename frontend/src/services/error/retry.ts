/**
 * 指数退避重试工具
 */

import type { ErrorCategory, RetryConfig } from './types';
import { RETRY_CONFIG } from './types';

/** 睡眠函数 */
const sleep = (ms: number): Promise<void> =>
  new Promise(resolve => setTimeout(resolve, ms));

/**
 * 带指数退避的重试执行
 *
 * @param action - 需要重试的异步操作
 * @param category - 错误类别（决定重试配置）
 * @param config - 可选的自定义重试配置（覆盖默认值）
 * @returns 操作结果
 * @throws 所有重试失败后抛出最后一个错误
 */
export async function retryWithBackoff<T>(
  action: () => Promise<T>,
  category?: ErrorCategory,
  config?: Partial<RetryConfig>,
): Promise<T> {
  const retryCfg = { ...(category ? RETRY_CONFIG[category] : RETRY_CONFIG.UNKNOWN), ...config };
  let lastError: Error | null = null;

  // Infinity 重试需要特殊处理
  const maxAttempts = retryCfg.maxRetries === Infinity
    ? Number.MAX_SAFE_INTEGER
    : retryCfg.maxRetries + 1;

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      const result = await action();
      return result;
    } catch (err) {
      lastError = err instanceof Error ? err : new Error(String(err));

      if (attempt < maxAttempts - 1) {
        const delay = Math.min(
          retryCfg.backoffMs * Math.pow(2, attempt),
          retryCfg.maxBackoffMs,
        );
        console.warn(`Retry ${attempt + 1}/${maxAttempts} in ${delay}ms (error: ${lastError.message})`);
        await sleep(delay);
      }
    }
  }

  throw new Error(
    `Retry failed after ${retryCfg.maxRetries === Infinity ? 'many' : retryCfg.maxRetries} attempts. Last error: ${lastError?.message}`,
    { cause: lastError },
  );
}
