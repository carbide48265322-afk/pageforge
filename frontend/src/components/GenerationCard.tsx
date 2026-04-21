import { Eye } from "lucide-react";

/** GenerationCard 组件的 props */
interface GenerationCardProps {
    /** 是否正在生成中 */
    isLoading: boolean;
    /** 生成的版本号（完成后显示） */
    version: number;
    /** 用户原始需求 */
    requirement: string;
    /** 点击查看预览回调 */
    onPreview: () => void;
    /** 工作流阶段信息 */
    workflowStage: { stage: string; label: string; color: string } | null;
}

/**
 * 页面生成卡片组件
 * 生成中显示骨架动画，完成后显示版本信息和预览按钮
 */
export function GenerationCard({
    isLoading,
    version,
    requirement,
    onPreview,
    workflowStage,
}: GenerationCardProps) {
    if (isLoading) {
        return (
            <div className="mb-4 rounded-lg border border-gray-200 bg-white px-4 py-3">
                {/* 标题行 */}
                <div className="flex items-center gap-2 mb-3">
                    <div className="w-4 h-4 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
                    <span className="text-sm text-gray-600">
                        {workflowStage ? `${workflowStage.label}...` : "正在生成页面..."}
                    </span>
                    {workflowStage && (
                        <span className={`text-xs font-medium ${workflowStage.color}`}>
                            {workflowStage.label}
                        </span>
                    )}
                </div>
                {/* 骨架条 */}
                <div className="space-y-2">
                    <div className="h-3 bg-gray-100 rounded animate-pulse w-3/4" />
                    <div className="h-3 bg-gray-100 rounded animate-pulse w-1/2" />
                    <div className="h-3 bg-gray-100 rounded animate-pulse w-5/6" />
                </div>
            </div>
        );
    }

    return (
        <div className="mb-4 rounded-lg border border-green-200 bg-green-50 px-4 py-3">
            <div className="flex items-center justify-between">
                <div>
                    <div className="flex items-center gap-2">
                        <span className="text-green-600 text-sm">✅</span>
                        <span className="text-sm font-medium text-gray-900">
                            页面已生成 (v{version})
                        </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1 truncate max-w-[300px]">
                        {requirement}
                    </p>
                </div>
                <button
                    onClick={onPreview}
                    className="flex items-center gap-1 px-3 py-1.5 text-xs rounded-lg
                        bg-blue-600 text-white hover:bg-blue-700 transition-colors shrink-0"
                >
                    <Eye size={12} />
                    查看预览
                </button>
            </div>
        </div>
    );
}