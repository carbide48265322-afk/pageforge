import { useState, useRef, useEffect } from "react";
import { GitBranch, ChevronDown } from "lucide-react";
import type { PageVersion } from "../services/api";

/** VersionSelector 组件的 props */
interface VersionSelectorProps {
    /** 版本列表 */
    versions: PageVersion[];
    /** 当前基准版本号 */
    currentBase: number;
    /** 选择版本回调（弹出确认） */
    onSelectVersion: (version: PageVersion) => void;
}

/**
 * 版本选择器组件
 * 下拉展示历史版本列表，点击版本触发基准版本切换确认
 */
export function VersionSelector({
    versions,
    currentBase,
    onSelectVersion,
}: VersionSelectorProps) {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // 点击外部关闭下拉
    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    // 没有版本时不渲染
    if (versions.length === 0) return null;

    return (
        <div className="relative" ref={dropdownRef}>
            {/* 触发按钮 */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-1.5 px-2 py-1 text-xs rounded
                    border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
            >
                <GitBranch size={12} />
                <span>v{currentBase}</span>
                <ChevronDown size={12} className={`transition-transform ${isOpen ? "rotate-180" : ""}`} />
            </button>

            {/* 下拉列表 */}
            {isOpen && (
                <div className="absolute right-0 top-full mt-1 w-64 bg-white border border-gray-200
                    rounded-lg shadow-lg z-20 max-h-60 overflow-y-auto">
                    <div className="px-3 py-2 text-xs text-gray-400 border-b border-gray-100">
                        版本历史（点击切换基准版本）
                    </div>
                    {versions.map((v) => (
                        <button
                            key={v.version}
                            onClick={() => {
                                onSelectVersion(v);
                                setIsOpen(false);
                            }}
                            className={`w-full text-left px-3 py-2 text-xs hover:bg-gray-50 transition-colors
                                border-b border-gray-50 last:border-b-0
                                ${v.version === currentBase ? "bg-blue-50 text-blue-700" : "text-gray-700"}`}
                        >
                            <div className="flex items-center justify-between">
                                <span className="font-medium">v{v.version}</span>
                                <span className="text-gray-400">
                                    {new Date(v.timestamp).toLocaleTimeString()}
                                </span>
                            </div>
                            <div className="text-gray-400 mt-0.5 truncate">{v.summary}</div>
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}