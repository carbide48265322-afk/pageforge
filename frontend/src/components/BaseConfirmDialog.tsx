import { useState } from "react";
import { AlertTriangle } from "lucide-react";
import type { PageVersion } from "../services/api";

/** BaseConfirmDialog 组件的 props */
interface BaseConfirmDialogProps {
    /** 要切换到的目标版本 */
    targetVersion: PageVersion;
    /** 当前基准版本号 */
    currentBase: number;
    /** 确认切换回调 */
    onConfirm: () => Promise<void>;
    /** 取消回调 */
    onCancel: () => void;
}

/**
 * 基准版本切换确认弹窗
 * 提示用户切换基准版本的影响，防止误操作
 */
export function BaseConfirmDialog({
    targetVersion,
    currentBase,
    onConfirm,
    onCancel,
}: BaseConfirmDialogProps) {
    const [isSubmitting, setIsSubmitting] = useState(false);

    /** 确认切换（防止重复提交） */
    const handleConfirm = async () => {
        if (isSubmitting) return;
        setIsSubmitting(true);
        try {
            await onConfirm();
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* 遮罩层 */}
            <div
                className="absolute inset-0 bg-black/30"
                onClick={onCancel}
            />

            {/* 弹窗内容 */}
            <div className="relative bg-white rounded-lg shadow-xl max-w-sm w-full mx-4 p-6">
                {/* 警告图标 */}
                <div className="flex items-center gap-3 mb-4">
                    <div className="flex items-center justify-center w-10 h-10 rounded-full bg-amber-100">
                        <AlertTriangle size={20} className="text-amber-600" />
                    </div>
                    <h3 className="text-sm font-medium text-gray-900">
                        切换基准版本
                    </h3>
                </div>

                {/* 提示信息 */}
                <p className="text-sm text-gray-600 mb-4">
                    将基准版本从 <span className="font-medium">v{currentBase}</span> 切换到{" "}
                    <span className="font-medium">v{targetVersion.version}</span>。
                    后续修改将基于 v{targetVersion.version} 的内容进行。
                </p>

                {/* 目标版本摘要 */}
                <div className="bg-gray-50 rounded-lg px-3 py-2 mb-6">
                    <p className="text-xs text-gray-500 truncate">
                        {targetVersion.summary}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                        {new Date(targetVersion.timestamp).toLocaleString()}
                    </p>
                </div>

                {/* 操作按钮 */}
                <div className="flex items-center justify-end gap-2">
                    <button
                        onClick={onCancel}
                        disabled={isSubmitting}
                        className="px-4 py-2 text-sm rounded-lg border border-gray-200
                            text-gray-600 hover:bg-gray-50 transition-colors
                            disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        取消
                    </button>
                    <button
                        onClick={handleConfirm}
                        disabled={isSubmitting}
                        className="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white
                            hover:bg-blue-700 transition-colors
                            disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isSubmitting ? "切换中..." : "确认切换"}
                    </button>
                </div>
            </div>
        </div>
    );
}