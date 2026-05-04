/**
 * PlanPanel - 计划步骤组件（P1.14）
 *
 * 接收 SSE 的 plan_start / plan_update / plan_done 事件
 * 展示 Agent 执行计划的步骤列表，实时高亮当前步骤
 * 垂直时间线布局，三态节点（pending/active/done）
 */

import React, { useState } from 'react';
import { Check, CheckCircle, ListChecks, ChevronDown, ChevronRight } from 'lucide-react';

import type { PlanBlock } from '../services/sse/types';

// ========== Props ==========

interface PlanPanelProps {
  plan: PlanBlock;
}

// ========== PulseDot 子组件（active 状态脉冲动画）==========

function PulseDot() {
  return (
    <span className="relative flex h-4 w-4">
      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-400 opacity-75" />
      <span className="relative inline-flex h-4 w-4 rounded-full bg-indigo-500" />
    </span>
  );
}

// ========== 主组件 ==========

export function PlanPanel({ plan }: PlanPanelProps) {
  const [expanded, setExpanded] = useState(true);

  // 统计各状态数量
  const doneCount = plan.steps.filter(s => s.status === 'done').length;
  const activeCount = plan.steps.filter(s => s.status === 'active').length;
  const totalCount = plan.steps.length;

  return (
    <div className="plan-panel border-l-2 border-indigo-400 bg-indigo-50/40 rounded-r-lg p-4">
      {/* 头部：图标 + 进度 + 折叠按钮 */}
      <header
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 cursor-pointer select-none"
      >
        <ListChecks size={16} className="shrink-0 text-indigo-600" />

        {/* 标题文字 */}
        <span className={`text-sm font-medium ${
          plan.isComplete ? 'text-green-700' : 'text-indigo-700'
        }`}>
          {plan.isComplete ? (
            <>
              计划完成
              <CheckCircle size={14} className="ml-1 inline text-green-500" />
            </>
          ) : (
            `执行计划 (${doneCount}/${totalCount})`
          )}
        </span>

        {/* 活跃步骤指示 */}
        {activeCount > 0 && !plan.isComplete && (
          <span className="inline-flex gap-0.5 ml-1">
            <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-pulse [animation-delay:0ms]" />
            <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-pulse [animation-delay:200ms]" />
          </span>
        )}

        {/* 展开/收起图标 */}
        {expanded ? (
          <ChevronDown size={14} className="ml-auto shrink-0 text-slate-400" />
        ) : (
          <ChevronRight size={14} className="ml-auto shrink-0 text-slate-400" />
        )}
      </header>

      {/* 步骤时间线内容区 */}
      {expanded && (
        <div className="mt-3 pl-1">
          <div className="steps-timeline">
            {plan.steps.map((step, index) => (
              <div key={step.id} className="flex gap-3">
                {/* 左侧：节点 + 连接线 */}
                <div className="flex flex-col items-center shrink-0">
                  {/* 圆形节点 */}
                  <div className={`
                    step-node flex items-center justify-center w-6 h-6 rounded-full border-2 text-[11px] font-medium transition-all duration-300
                    ${step.status === 'pending'
                      ? 'border-slate-300 bg-white text-slate-400'
                      : step.status === 'active'
                        ? 'border-indigo-500 bg-indigo-50'
                        : 'border-green-500 bg-green-500 text-white'
                    }
                  `}>
                    {step.status === 'done' && <Check size={12} />}
                    {step.status === 'active' && <PulseDot />}
                    {step.status === 'pending' && <span>{index + 1}</span>}
                  </div>

                  {/* 连接线（最后一个不画） */}
                  {index < plan.steps.length - 1 && (
                    <div className={`
                      connector w-0.5 h-6 mt-1 -mb-1 transition-colors duration-300
                      ${step.status === 'done'
                        ? 'bg-green-300'
                        : step.status === 'active'
                          ? 'bg-indigo-300'
                          : 'bg-slate-200'
                      }
                    `} />
                  )}
                </div>

                {/* 右侧：步骤文字标签 */}
                <span className={`
                  step-label pt-0.5 text-sm leading-relaxed min-w-0 break-words transition-colors duration-300
                  ${step.status === 'pending'
                    ? 'text-slate-400'
                    : step.status === 'active'
                      ? 'text-indigo-700 font-medium'
                      : 'text-slate-600'
                  }
                `}>
                  {step.label}
                </span>
              </div>
            ))}
          </div>

          {/* 完成标记 */}
          {plan.isComplete && (
            <div className="complete-badge mt-3 flex items-center justify-center gap-1.5 py-1.5 px-3 bg-green-100 text-green-700 text-xs font-medium rounded-full">
              <CheckCircle size={14} />
              全部步骤已完成
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default PlanPanel;
