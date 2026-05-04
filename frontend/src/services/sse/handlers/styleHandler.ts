/**
 * Style 事件处理器
 * 处理 style_selected 等事件
 */

import type { StyleConfig } from '../types';

// 当前风格配置
let currentStyle: StyleConfig | null = null;

export const styleHandler = {
  /**
   * 处理 style_selected 事件
   */
  onSelected(data: {
    style: string;
    primary_color?: string;
    description?: string;
    [key: string]: unknown;
  }): StyleConfig {
    currentStyle = {
      style: data.style,
      primary_color: data.primary_color,
      description: data.description,
      ...data,
    };

    // 移除已知字段，保留其他自定义字段
    delete currentStyle.style;
    delete currentStyle.primary_color;
    delete currentStyle.description;

    // 确保必需字段存在
    currentStyle = {
      style: data.style,
      primary_color: data.primary_color,
      description: data.description,
      ...currentStyle,
    };

    return currentStyle;
  },

  /**
   * 获取当前风格配置
   */
  getCurrent(): StyleConfig | null {
    return currentStyle;
  },

  /**
   * 重置状态
   */
  reset(): void {
    currentStyle = null;
  },
};
