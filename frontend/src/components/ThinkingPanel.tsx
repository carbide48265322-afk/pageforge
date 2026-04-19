import { Brain, Wrench, Loader2 } from "lucide-react";
import type { ThinkingStep } from "../hooks/useSSE";
import type { ToolCall } from "../services/api";

/** ThinkingPanel 组件的 props */
interface ThinkingPanelProps {
    /** 思考步骤列表 */
    thinkingSteps: ThinkingStep[];
    /** 当前正在执行的工具调用 */
    currentToolCall: ToolCall | null;
    /** 是否正在加载中 */
    isLoading: boolean;
}

/**
 * Agent 思考过程展示组件
 * 显示 Agent 的思考步骤和当前工具调用状态
 * 仅在 isLoading 时展示
 */
export function ThinkingPanel({
    thinkingSteps,
    currentToolCall,
    isLoading,
}: ThinkingPanelProps) {
    // 非加载状态不渲染
    if (!isLoading) return null;

    return (
        <div className="mb-4 rounded-lg border border-gray-200 bg-gray-50 px-4 py-3">
            {/* 标题栏 */}
            <div className="flex items-center gap-2 text-sm font-medium text-gray-600 mb-2">
                <Brain size={14} />
                <span>Agent 思考中</span>
                <Loader2 size={14} className="animate-spin" />
            </div>

            {/* 思考步骤列表 */}
            <div className="space-y-1">
                {thinkingSteps.map((step) => (
                    <div
                        key={step.index}
                        className="flex items-start gap-2 text-xs text-gray-500"
                    >
                        <span className="mt-0.5 shrink-0 w-4 h-4 rounded-full bg-gray-200 text-gray-600 flex items-center justify-center text-[10px]">
                            {step.index}
                        </span>
                        <span className="leading-relaxed">{step.content}</span>
                    </div>
                ))}

                {/* 当前工具调用（实时展示） */}
                {currentToolCall && (
                    <div className="flex items-center gap-2 text-xs text-blue-600 mt-2 pt-2 border-t border-gray-200">
                        <Wrench size={12} />
                        <span className="font-mono bg-blue-50 px-1.5 py-0.5 rounded">
                            {currentToolCall.tool}
                        </span>
                        <Loader2 size={12} className="animate-spin" />
                    </div>
                )}
            </div>
        </div>
    );
}