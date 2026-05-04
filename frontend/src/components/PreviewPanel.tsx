import { useState } from "react";
import { X, Eye, Code, Copy, Download, Check } from "lucide-react";
import { FileTree } from "./FileTree";
import { CodeViewer } from "./CodeViewer";
import type { FileNode, FileContent } from "./CodeViewer";
import type { PreviewSource } from "../hooks/useSSEv2";

/**
 * PreviewPanel 组件的 props
 * 新面板：支持预览/代码 Tab 切换
 */
interface PreviewPanelProps {
  /** 预览源（html/url/none） */
  previewSource: PreviewSource;
  /** 文件树数据 */
  files: FileNode[];
  /** 当前选中的文件路径 */
  selectedFile?: string;
  /** 文件选择回调 */
  onFileSelect: (path: string) => void;
  /** 是否打开面板 */
  isOpen: boolean;
  /** 关闭回调 */
  onClose: () => void;
}

/**
 * 新预览面板组件
 * 支持预览/代码 Tab 切换
 * - 预览 Tab：显示 HTML 或 URL 预览
 * - 代码 Tab：显示 FileTree + CodeViewer
 */
export function PreviewPanel({
  previewSource,
  files,
  selectedFile,
  onFileSelect,
  isOpen,
  onClose,
}: PreviewPanelProps) {
  const [activeTab, setActiveTab] = useState<"preview" | "code">("preview");
  const [copied, setCopied] = useState(false);

  // 获取当前选中的文件内容（从后端API获取）
  const [fileContent, setFileContent] = useState<FileContent | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(false);

  // 文件选择处理
  const handleFileSelect = (path: string) => {
    onFileSelect(path);
    loadFileContent(path);
  };

  // 加载文件内容
  const loadFileContent = async (path: string) => {
    setIsLoading(true);
    try {
      // TODO: 从后端 API 获取文件内容
      // const response = await api.getFileContent(sessionId, path);
      // setFileContent({ path, content: response.content, language: response.language });
      
      // 临时模拟数据
      setFileContent({
        path: path,
        content: "// 文件内容加载中...",
        language: path.split(".").pop() || "plaintext",
      });
    } catch (error) {
      console.error("加载文件内容失败:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // 复制 HTML 源码
  const handleCopy = async () => {
    if (previewSource.mode !== "html" || !previewSource.html) return;
    await navigator.clipboard.writeText(previewSource.html);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // 下载 HTML 文件
  const handleDownload = () => {
    if (previewSource.mode !== "html" || !previewSource.html) return;
    const blob = new Blob([previewSource.html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "page.html";
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!isOpen) return null;

  return (
    <div className="flex flex-col h-full bg-white border-l border-gray-200">
      {/* 顶部工具栏 */}
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-2">
        <div className="flex items-center gap-2">
          {/* Tab 切换 */}
          <button
            onClick={() => setActiveTab("preview")}
            className={`px-3 py-1 text-xs rounded transition-colors ${
              activeTab === "preview"
                ? "bg-blue-100 text-blue-700 font-medium"
                : "text-gray-400 hover:text-gray-600"
            }`}
          >
            <Eye size={12} className="inline mr-1" />
            预览
          </button>
          <button
            onClick={() => setActiveTab("code")}
            className={`px-3 py-1 text-xs rounded transition-colors ${
              activeTab === "code"
                ? "bg-blue-100 text-blue-700 font-medium"
                : "text-gray-400 hover:text-gray-600"
            }`}
          >
            <Code size={12} className="inline mr-1" />
            代码
          </button>
        </div>

        <div className="flex items-center gap-1">
          {/* 复制按钮（仅 html 模式） */}
          {previewSource.mode === "html" && (
            <button
              onClick={handleCopy}
              className="p-1.5 rounded text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
              title={copied ? "已复制" : "复制源码"}
            >
              {copied ? <Check size={16} className="text-green-500" /> : <Copy size={16} />}
            </button>
          )}

          {/* 下载按钮（仅 html 模式） */}
          {previewSource.mode === "html" && (
            <button
              onClick={handleDownload}
              className="p-1.5 rounded text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
              title="下载 HTML"
            >
              <Download size={16} />
            </button>
          )}

          {/* 收起按钮 */}
          <button
            onClick={onClose}
            className="p-1.5 rounded text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
            title="收起面板"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="flex-1 overflow-hidden">
        {/* 预览 Tab */}
        {activeTab === "preview" && (
          <div className="h-full bg-gray-100 p-4">
            {previewSource.mode === "none" ? (
              <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                暂无预览内容
              </div>
            ) : previewSource.mode === "html" ? (
              <div className="h-full bg-white rounded-lg shadow-lg overflow-hidden">
                <iframe
                  srcDoc={previewSource.html}
                  sandbox="allow-scripts"
                  className="w-full h-full border-0"
                  title="页面预览"
                />
              </div>
            ) : (
              <div className="h-full bg-white rounded-lg shadow-lg overflow-hidden">
                <iframe
                  src={previewSource.url}
                  className="w-full h-full border-0"
                  title="应用预览"
                />
              </div>
            )}
          </div>
        )}

        {/* 代码 Tab */}
        {activeTab === "code" && (
          <div className="h-full flex">
            {/* 文件树 */}
            <div className="w-64 border-r border-gray-200 bg-gray-50 overflow-y-auto">
              <FileTree
                files={files}
                onSelect={handleFileSelect}
                selectedPath={selectedFile}
              />
            </div>

            {/* 代码查看器 */}
            <div className="flex-1 overflow-hidden">
              <CodeViewer file={fileContent} isLoading={isLoading} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
