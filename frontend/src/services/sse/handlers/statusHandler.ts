/**
 * Status 事件处理器
 * 处理 status:* 系列事件
 */

import type { WebContainerPhase, StatusEvent } from '../types';

// 当前状态
let currentStatus: StatusEvent = {
  phase: 'idle',
};

export const statusHandler = {
  onInit(data: { message?: string }): StatusEvent {
    currentStatus = {
      phase: 'idle',
      message: data.message || '初始化...',
    };
    return currentStatus;
  },

  onInstalling(data: { message?: string }): StatusEvent {
    currentStatus = {
      phase: 'installing',
      message: data.message || '正在安装依赖...',
    };
    return currentStatus;
  },

  onInstallDone(data: { message?: string }): StatusEvent {
    currentStatus = {
      phase: 'ready',
      message: data.message || '依赖安装完成',
    };
    return currentStatus;
  },

  onGenerationDone(data: { message?: string }): StatusEvent {
    currentStatus = {
      ...currentStatus,
      phase: 'ready',
      message: data.message || '生成完成',
    };
    return currentStatus;
  },

  onStartingDev(data: { port?: number; message?: string }): StatusEvent {
    currentStatus = {
      phase: 'running',
      message: data.message || `Dev Server 启动中 (端口 ${data.port || 3000})`,
    };
    return currentStatus;
  },

  onPreviewReady(data: { url?: string; message?: string }): StatusEvent {
    currentStatus = {
      phase: 'running',
      message: data.message || '预览就绪',
    };
    return currentStatus;
  },

  /**
   * 获取当前状态
   */
  getCurrent(): StatusEvent {
    return currentStatus;
  },

  /**
   * 重置状态
   */
  reset(): void {
    currentStatus = { phase: 'idle' };
  },
};
