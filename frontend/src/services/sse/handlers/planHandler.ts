/**
 * Plan 事件处理器
 * 处理 plan_start / plan_update / plan_done 事件
 */

import type { PlanBlock, PlanStep } from '../types';

// 当前活跃的 PlanBlock（内部状态）
let currentPlan: PlanBlock | null = null;

export const planHandler = {
  /**
   * 处理 plan_start 事件
   * data: { steps: [{id, label}], current: 0 }
   */
  onStart(data: { steps: Omit<PlanStep, 'status'>[]; current: number; id?: string }): PlanBlock {
    const steps: PlanStep[] = data.steps.map((step, index) => ({
      ...step,
      status: index < data.current ? 'done' : index === data.current ? 'active' : 'pending',
    }));

    currentPlan = {
      type: 'plan',
      id: data.id || `plan_${Date.now()}`,
      steps,
      currentStep: data.current,
      isComplete: false,
    };

    return currentPlan;
  },

  /**
   * 处理 plan_update 事件
   * data: { steps: [...], current: N }
   */
  onUpdate(data: { steps: Omit<PlanStep, 'status'>[]; current: number }): PlanBlock | null {
    if (!currentPlan) {
      console.warn('plan_update: no matching plan_start');
      return null;
    }

    const steps: PlanStep[] = data.steps.map((step, index) => ({
      ...step,
      status: index < data.current ? 'done' : index === data.current ? 'active' : 'pending',
    }));

    currentPlan.steps = steps;
    currentPlan.currentStep = data.current;

    return currentPlan;
  },

  /**
   * 处理 plan_done 事件
   */
  onDone(data: { steps: Omit<PlanStep, 'status'>[] }): PlanBlock | null {
    if (!currentPlan) {
      console.warn('plan_done: no matching plan_start');
      return null;
    }

    // 所有步骤标记完成
    currentPlan.steps = data.steps.map(step => ({
      ...step,
      status: 'done' as const,
    }));
    currentPlan.isComplete = true;

    const result = currentPlan;
    currentPlan = null; // 重置
    return result;
  },

  /**
   * 获取当前 plan 状态
   */
  getCurrent(): PlanBlock | null {
    return currentPlan;
  },

  /**
   * 重置状态
   */
  reset(): void {
    currentPlan = null;
  },
};
