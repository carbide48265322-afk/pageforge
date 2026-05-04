import { useState, type ReactNode } from "react";
import { ChevronRight, ChevronDown, File, Folder, FolderOpen } from "lucide-react";

/**
 * 文件树节点类型
 */
export interface FileNode {
  type: "file" | "folder";
  name: string;
  path: string;
  children?: FileNode[];
  language?: string;  // 文件语言（用于图标显示）
}

/** FileTree 组件的 props */
interface FileTreeProps {
  files: FileNode[];
  onSelect: (path: string) => void;
  selectedPath?: string;
}

/**
 * 获取文件语言对应的图标颜色
 */
function getLanguageColor(language?: string): string {
  const colorMap: Record<string, string> = {
    typescript: "text-blue-600",
    javascript: "text-yellow-600",
    tsx: "text-blue-400",
    jsx: "text-yellow-400",
    css: "text-pink-500",
    html: "text-orange-600",
    json: "text-yellow-700",
    markdown: "text-gray-600",
  };
  return colorMap[language || ""] || "text-gray-500";
}

/**
 * 获取文件语言显示名称
 */
function getLanguageLabel(language?: string): string {
  const labelMap: Record<string, string> = {
    typescript: "TS",
    javascript: "JS",
    tsx: "TSX",
    jsx: "JSX",
    css: "CSS",
    html: "HTML",
    json: "JSON",
    markdown: "MD",
  };
  return labelMap[language || ""] || "";
}

/**
 * 递归渲染文件树节点
 */
function FileTreeNode({
  node,
  depth,
  onSelect,
  selectedPath,
}: {
  node: FileNode;
  depth: number;
  onSelect: (path: string) => void;
  selectedPath?: string;
}) {
  const [isExpanded, setIsExpanded] = useState(depth < 2);  // 默认展开前两层
  const isSelected = selectedPath === node.path;

  const handleClick = () => {
    if (node.type === "folder") {
      setIsExpanded(!isExpanded);
    } else {
      onSelect(node.path);
    }
  };

  return (
    <div>
      {/* 当前节点 */}
      <div
        onClick={handleClick}
        className={`
          flex items-center gap-1.5 px-2 py-1 cursor-pointer rounded
          transition-colors text-sm
          ${isSelected ? "bg-blue-100 text-blue-700" : "hover:bg-gray-100 text-gray-700"}
        `}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
      >
        {node.type === "folder" ? (
          <>
            {isExpanded ? (
              <ChevronDown size={14} className="text-gray-400" />
            ) : (
              <ChevronRight size={14} className="text-gray-400" />
            )}
            {isExpanded ? (
              <FolderOpen size={14} className="text-yellow-500" />
            ) : (
              <Folder size={14} className="text-yellow-500" />
            )}
          </>
        ) : (
          <>
            <span className="w-3.5" />  {/* 占位对齐 */}
            <File size={14} className={getLanguageColor(node.language)} />
          </>
        )}
        
        <span className="flex-1 truncate">{node.name}</span>
        
        {node.type === "file" && node.language && (
          <span className={`text-xs font-mono ${getLanguageColor(node.language)}`}>
            {getLanguageLabel(node.language)}
          </span>
        )}
      </div>

      {/* 子节点（文件夹展开时显示） */}
      {node.type === "folder" && isExpanded && node.children && (
        <div>
          {node.children.map((child) => (
            <FileTreeNode
              key={child.path}
              node={child}
              depth={depth + 1}
              onSelect={onSelect}
              selectedPath={selectedPath}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * 文件树组件
 * 支持文件夹展开/折叠、文件图标、点击选择
 */
export function FileTree({ files, onSelect, selectedPath }: FileTreeProps) {
  if (!files || files.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400 text-sm">
        暂无文件
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto py-2">
      {files.map((node) => (
        <FileTreeNode
          key={node.path}
          node={node}
          depth={0}
          onSelect={onSelect}
          selectedPath={selectedPath}
        />
      ))}
    </div>
  );
}
