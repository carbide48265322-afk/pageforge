import { FolderOpen, Search, GitBranch, RefreshCw, Settings, Plus } from "lucide-react";
import { FileTree } from "./FileTree";
import { CodeViewer } from "./CodeViewer";
import type { FileNode, FileContent } from "./CodeViewer";

/**
 * CodePanel 组件的 props
 */
interface CodePanelProps {
  /** 文件树数据 */
  files: FileNode[];
  /** 当前选中的文件路径 */
  selectedFile?: string;
  /** 文件选择回调 */
  onSelect: (path: string) => void;
  /** 当前选中的文件内容 */
  fileContent?: FileContent;
  /** 是否正在加载 */
  isLoading?: boolean;
}

/**
 * 代码面板组件
 * 包含文件树和代码查看器的组合组件
 */
export function CodePanel({
  files,
  selectedFile,
  onSelect,
  fileContent,
  isLoading,
}: CodePanelProps) {
  return (
    <div className="h-full flex">
      {/* 侧边按钮栏 */}
      <div className="w-12 border-r border-gray-200 bg-gray-50 flex flex-col items-center py-2 gap-1 overflow-hidden">
        <button className="flex items-center justify-center w-8 h-8 rounded hover:bg-gray-200 transition-colors text-gray-600 hover:text-gray-900" title="项目">
          <FolderOpen size={18} />
        </button>
        <button className="flex items-center justify-center w-8 h-8 rounded hover:bg-gray-200 transition-colors text-gray-600 hover:text-gray-900" title="搜索">
          <Search size={18} />
        </button>
        <button className="flex items-center justify-center w-8 h-8 rounded hover:bg-gray-200 transition-colors text-gray-600 hover:text-gray-900" title="分支">
          <GitBranch size={18} />
        </button>
        <button className="flex items-center justify-center w-8 h-8 rounded hover:bg-gray-200 transition-colors text-gray-600 hover:text-gray-900" title="刷新">
          <RefreshCw size={18} />
        </button>
        <button className="flex items-center justify-center w-8 h-8 rounded hover:bg-gray-200 transition-colors text-gray-600 hover:text-gray-900" title="设置">
          <Settings size={18} />
        </button>
        <div className="flex-1" />
        <button className="flex items-center justify-center w-8 h-8 rounded hover:bg-gray-200 transition-colors text-gray-600 hover:text-gray-900" title="新建">
          <Plus size={18} />
        </button>
      </div>

      {/* 文件树 */}
      <div className="w-56 border-r border-gray-200 flex flex-col">
        {/* 固定标题栏 */}
        <div className="px-3 py-2 border-b border-gray-200 text-xs font-medium text-gray-500 bg-gray-50 flex-shrink-0">
          Project
        </div>
        {/* 可滚动内容区域 */}
        <div className="flex-1 overflow-y-auto">
          <FileTree
            files={files}
            onSelect={onSelect}
            selectedPath={selectedFile}
          />
        </div>
      </div>

      {/* 代码查看器 */}
      <div className="flex-1 overflow-hidden">
        <CodeViewer file={fileContent} isLoading={isLoading} />
      </div>
    </div>
  );
}
