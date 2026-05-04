/**
 * StatusBar - 底部状态栏组件（P1.16）
 *
 * 固定在页面底部，全局展示当前项目的关键状态信息：
 * - 项目类型（React+Vite / HTML单页）
 * - 文件数量
 * - WebContainer 状态（初始化/安装/就绪/运行/出错）
 * - Dev Server 状态
 * - Session ID
 *
 * 放在 App.tsx 最外层布局最底部，不受 ResizableLayout 影响
 */

import React from 'react';
import {
  Package,
  Server,
  Wifi,
  WifiOff,
  AlertCircle,
  Loader2,
  CheckCircle,
  Play,
} from 'lucide-react';

import type { WebContainerPhase } from '../services/sse/types';

// ========== Props ==========

interface StatusBarProps {
  /** 项目类型标识，如 "react-vite-app" */
  projectType?: string;
  /** 文件数量 */
  fileCount: number;
  /** WebContainer 当前阶段 */
  webContainerPhase: WebContainerPhase;
  /** Dev Server 是否运行中 */
  devServerRunning: boolean;
  /** 当前 Session ID（短显示） */
  sessionId: string;
}

// ========== 项目类型显示名映射 ==========

const PROJECT_TYPE_LABELS: Record<string, string> = {
  'react-vite-app': 'React + Vite',
  'html-single': 'HTML 单页',
};

// ========== WebContainer 阶段配置 ==========

const PHASE_CONFIG: Record<WebContainerPhase, {
  label: string;
  icon: React.ReactNode;
  textColor: string;
}> = {
  idle: {
    label: '未启动',
    icon: <WifiOff size={12} />,
    textColor: 'text-slate-400',
  },
  booting: {
    label: '启动中...',
    icon: <Loader2 size={12} className="animate-spin" />,
    textColor: 'text-amber-600',
  },
  installing: {
    label: '安装依赖...',
    icon: <Package size={12} />,
    textColor: 'text-amber-600',
  },
  ready: {
    label: 'WebContainer 就绪',
    icon: <CheckCircle size={12} />,
    textColor: 'text-green-600',
  },
  running: {
    label: 'Dev Server 运行中',
    icon: <Play size={12} />,
    textColor: 'text-indigo-600',
  },
  error: {
    label: '出错',
    icon: <AlertCircle size={12} />,
    textColor: 'text-red-500',
  },
};

// ========== 主组件 ==========

export function StatusBar({
  projectType,
  fileCount,
  webContainerPhase,
  devServerRunning,
  sessionId,
}: StatusBarProps) {
  const phaseConfig = PHASE_CONFIG[webContainerPhase];
  const projectLabel = projectType ? (PROJECT_TYPE_LABELS[projectType] || projectType) : null;

  return (
    <footer className="
      status-bar
      h-8
      border-t border-slate-200
      px-4
      flex items-center justify-between
      bg-white/95 backdrop-blur-sm
      sticky bottom-0 z-50
      select-none
    ">
      {/* 左侧：项目类型 + 文件数量 */}
      <div className="left-section flex items-center gap-3">
        {projectLabel && (
          <span className="project-badge inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-100 text-[11px] font-medium text-slate-600">
            {projectLabel}
          </span>
        )}

        <span className="file-count flex items-center gap-1 text-[11px] text-slate-500">
          <Package size={11} />
          {fileCount} 个文件
        </span>
      </div>

      {/* 中间：服务状态 */}
      <div className="center-section flex items-center gap-2">
        {/* WebContainer 状态 */}
        <span className={`
          wc-status inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium
          ${webContainerPhase === 'ready'
            ? 'bg-green-50 text-green-600'
            : webContainerPhase === 'running'
              ? 'bg-indigo-50 text-indigo-600'
              : webContainerPhase === 'error'
                ? 'bg-red-50 text-red-500'
                : ['booting', 'installing'].includes(webContainerPhase)
                  ? 'bg-amber-50 text-amber-600'
                  : 'bg-slate-50 text-slate-400'
          }
        `}>
          {phaseConfig.icon}
          {phaseConfig.label}
        </span>

        {/* Dev Server 分隔符 + 状态 */}
        {devServerRunning && (
          <>
            <span className="text-slate-300">·</span>
            <span className="dev-status inline-flex items-center gap-1 text-[11px] font-medium text-indigo-600">
              <Server size={11} />
              pnpm run dev
            </span>
          </>
        )}

        {/* 未连接提示 */}
        {webContainerPhase === 'idle' && !devServerRunning && (
          <span className="idle-hint text-[11px] text-slate-400">
            等待项目生成...
          </span>
        )}
      </div>

      {/* 右侧：Session ID */}
      <div className="right-section">
        <code className="text-[10px] text-slate-400 font-mono tracking-tight">
          {sessionId.slice(0, 8)}
        </code>
      </div>
    </footer>
  );
}

// ========== 默认导出 ==========

export default StatusBar;
