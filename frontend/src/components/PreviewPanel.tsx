import { useState, useEffect } from "react";
import { Eye, Code, FileText, Monitor, Tablet, Smartphone, RefreshCw, Maximize, Edit3, ChevronDown, Minus, Plus } from "lucide-react";
import { CodePanel } from "./CodePanel";
import type { FileNode, FileContent } from "./CodeViewer";
import type { PreviewSource } from "../hooks/useSSEv2";
import { getFiles, getFileContent } from "../services/api";

type DeviceType = "desktop" | "tablet" | "mobile";

interface DeviceModel {
  id: string;
  name: string;
  width: number;
  height: number;
}

const deviceModels: Record<Exclude<DeviceType, "desktop">, DeviceModel[]> = {
  tablet: [
    { id: "ipad-pro", name: "iPad Pro", width: 1024, height: 1366 },
    { id: "ipad-air", name: "iPad Air", width: 820, height: 1180 },
    { id: "ipad-mini", name: "iPad mini", width: 768, height: 1024 },
    { id: "galaxy-tab", name: "Galaxy Tab", width: 800, height: 1280 },
  ],
  mobile: [
    { id: "iphone-16-pro-max", name: "iPhone 16 Pro Max", width: 430, height: 932 },
    { id: "iphone-16-pro", name: "iPhone 16 Pro", width: 393, height: 852 },
    { id: "iphone-15-pro", name: "iPhone 15 Pro", width: 393, height: 852 },
    { id: "iphone-15", name: "iPhone 15", width: 393, height: 852 },
    { id: "samsung-s24", name: "Samsung S24", width: 360, height: 756 },
  ],
};

const zoomLevels = [25, 50, 75, 100, 125, 150, 200];

/**
 * PreviewPanel 组件的 props
 * 新面板：支持预览/代码 Tab 切换
 */
interface PreviewPanelProps {
    /** 会话 ID */
    sessionId: string;
    /** 预览源（html/url/none） */
    previewSource: PreviewSource;
    /** 文件树数据 */
    files: FileNode[];
    /** 当前选中的文件路径 */
    selectedFile?: string;
    /** 文件选择回调 */
    onFileSelect: (path: string) => void;
}

// 辅助函数：将扁平文件列表转换为树形结构
function buildFileTree(flatFiles: Array<{ path: string; type: string }>): FileNode[] {
    const tree: Record<string, FileNode> = {};
    const roots: FileNode[] = [];

    // 先初始化所有节点
    flatFiles.forEach(file => {
        tree[file.path] = {
            type: file.type === "directory" ? "folder" : "file",
            name: file.path.split("/").pop() || "",
            path: file.path,
            children: file.type === "directory" ? [] : undefined,
            language: getFileLanguage(file.path),
        };
    });

    // 构建父子关系
    flatFiles.forEach(file => {
        const parts = file.path.split("/");
        if (parts.length === 1) {
            // 根目录文件
            roots.push(tree[file.path]);
        } else {
            // 找到父目录
            const parentPath = parts.slice(0, -1).join("/");
            const parent = tree[parentPath];
            if (parent && parent.children) {
                parent.children.push(tree[file.path]);
            }
        }
    });

    // 按字母顺序排序
    const sortNodes = (nodes: FileNode[]) => {
        nodes.sort((a, b) => {
            // 文件夹优先
            if (a.type !== b.type) return a.type === "folder" ? -1 : 1;
            return a.name.localeCompare(b.name);
        });
        nodes.forEach(node => {
            if (node.children) sortNodes(node.children);
        });
    };
    sortNodes(roots);

    return roots;
}

// 辅助函数：根据文件扩展名获取语言
function getFileLanguage(path: string): string | undefined {
    const ext = path.split(".").pop()?.toLowerCase();
    const langMap: Record<string, string> = {
        ts: "TypeScript",
        tsx: "TSX",
        js: "JavaScript",
        jsx: "JSX",
        css: "CSS",
        html: "HTML",
        json: "JSON",
        md: "Markdown",
        py: "Python",
        yml: "YAML",
        yaml: "YAML",
        toml: "TOML",
    };
    return langMap[ext || ""];
}

/**
 * 新预览面板组件
 * 支持预览/代码 Tab 切换
 * - 预览 Tab：显示 HTML 或 URL 预览
 * - 代码 Tab：显示 FileTree + CodeViewer
 */
export function PreviewPanel({
    sessionId,
    previewSource,
    files: initialFiles,
    selectedFile,
    onFileSelect,
}: PreviewPanelProps) {
    const [activeTab, setActiveTab] = useState<"preview" | "code">("preview");

    // 获取当前选中的文件内容（从后端 API 获取）
    const [fileContent, setFileContent] = useState<FileContent | undefined>(undefined);
    const [isLoading, setIsLoading] = useState(false);

    // 从后端获取的文件树数据
    const [fileTree, setFileTree] = useState<FileNode[]>([]);

    // 预览设备相关状态
    const [deviceType, setDeviceType] = useState<DeviceType>("mobile");
    const [selectedModel, setSelectedModel] = useState<DeviceModel | null>(deviceModels.mobile[0]);
    const [zoom, setZoom] = useState(100);
    const [showDeviceDropdown, setShowDeviceDropdown] = useState(false);

    // 临时演示数据，实际使用时应该从 props 传入
    const effectivePreviewSource: PreviewSource = previewSource.mode === "none" ? {
        mode: "html",
        html: `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>演示页面</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { 
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    .container {
      background: white;
      border-radius: 20px;
      padding: 30px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.2);
      text-align: center;
      max-width: 350px;
    }
    .title {
      font-size: 24px;
      font-weight: 700;
      color: #1a1a2e;
      margin-bottom: 10px;
    }
    .subtitle {
      font-size: 14px;
      color: #666;
      margin-bottom: 30px;
    }
    .button {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      padding: 14px 30px;
      border-radius: 10px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .button:hover {
      transform: translateY(-2px);
      box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
    }
    .icon {
      font-size: 60px;
      margin-bottom: 20px;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="icon">🎉</div>
    <h1 class="title">预览功能正常</h1>
    <p class="subtitle">设备视图切换已配置完成</p>
    <button class="button">开始使用</button>
  </div>
</body>
</html>
`
    } : previewSource;

    // 从后端获取文件列表
    useEffect(() => {
        // 先使用传入的 initialFiles
        if (initialFiles.length > 0) {
            setFileTree(initialFiles);
            return;
        }

        // 从后端获取
        let isMounted = true;
        async function fetchFiles() {
            try {
                const data = await getFiles(sessionId);
                if (isMounted && data.success && data.files) {
                    const tree = buildFileTree(data.files);
                    setFileTree(tree);
                }
            } catch (error) {
                console.error("获取文件列表失败:", error);
            }
        }
        fetchFiles();
        return () => { isMounted = false; };
    }, [sessionId, initialFiles]);

    // 文件选择处理
    const handleFileSelect = (path: string) => {
        onFileSelect(path);
        loadFileContent(path);
    };

    // 加载文件内容
    const loadFileContent = async (path: string) => {
        setIsLoading(true);
        try {
            const response = await getFileContent(sessionId, path);
            setFileContent({
                path: path,
                content: response.content,
                language: path.split(".").pop() || "plaintext",
            });
        } catch (error) {
            console.error("加载文件内容失败:", error);
            setFileContent({
                path: path,
                content: "// 加载文件内容失败",
                language: path.split(".").pop() || "plaintext",
            });
        } finally {
            setIsLoading(false);
        }
    };

  return (
    <div className="flex flex-col h-full p-2">
      {/* 顶部工具栏 */}
      <div className="flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg">
        {/* Tab 切换 */}
        <div className="flex items-center gap-0.5">
          <button
            onClick={() => setActiveTab("code")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-t-lg transition-colors ${activeTab === "code"
                ? "bg-gray-50 text-gray-900 font-medium"
                : "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
              }`}
          >
            <Code size={12} />
            代码
          </button>
          <button
            onClick={() => setActiveTab("preview")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-t-lg transition-colors ${activeTab === "preview"
                ? "bg-gray-50 text-gray-900 font-medium"
                : "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
              }`}
          >
            <Eye size={12} />
            预览
          </button>
          <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-t-lg transition-colors text-gray-500 hover:text-gray-700 hover:bg-gray-100">
            <FileText size={12} />
            文件
          </button>
          <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-t-lg transition-colors text-gray-500 hover:text-gray-700 hover:bg-gray-100">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
            </svg>
            云服务
          </button>
        </div>

        {/* 右侧按钮 */}
        <div className="flex items-center gap-1">
          <button className="flex items-center justify-center size-6 rounded hover:bg-gray-100 transition-colors">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gray-500">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="8" y1="12" x2="16" y2="12"></line>
            </svg>
          </button>
          <button className="flex items-center justify-center size-6 rounded hover:bg-gray-100 transition-colors">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gray-500">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
          </button>
          <button className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-white bg-gray-900 rounded hover:bg-gray-800 transition-colors">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
            发布
          </button>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="flex-1 mt-2 overflow-hidden bg-white border border-gray-200 rounded-lg">
        {/* 预览 Tab */}
        {activeTab === "preview" && (
          <div className="h-full flex flex-col">
            {/* 预览顶部按钮栏 */}
            <div className="h-10 bg-gray-50 flex items-center justify-between px-3 border-b border-gray-200">
              {/* 左侧 - 视图切换 */}
              <div className="flex items-center gap-0.5">
                {/* 视图模式切换 */}
                <div className="flex bg-gray-200 rounded">
                  <button
                    onClick={() => {
                      setDeviceType("desktop");
                      setSelectedModel(null);
                      setShowDeviceDropdown(false);
                    }}
                    className={`flex items-center justify-center w-8 h-8 rounded-l transition-colors ${
                      deviceType === "desktop" ? "bg-gray-300 text-gray-900" : "text-gray-500 hover:text-gray-700"
                    }`}
                  >
                    <Monitor size={16} />
                  </button>
                  <button
                    onClick={() => {
                      if (deviceType !== "mobile") {
                        setDeviceType("mobile");
                        setSelectedModel(deviceModels.mobile[0]);
                      }
                      setShowDeviceDropdown(false);
                    }}
                    className={`flex items-center justify-center w-8 h-8 rounded-r transition-colors ${
                      deviceType !== "desktop" ? "bg-gray-300 text-gray-900" : "text-gray-500 hover:text-gray-700"
                    }`}
                  >
                    <Smartphone size={16} />
                  </button>
                </div>

                <div className="w-px h-6 bg-gray-300 mx-2" />

                {/* 刷新按钮 */}
                <button className="flex items-center justify-center w-8 h-8 rounded text-gray-500 hover:text-gray-700 hover:bg-gray-100">
                  <RefreshCw size={16} />
                </button>

                {/* 其他按钮 */}
                <button className="flex items-center justify-center w-8 h-8 rounded text-gray-500 hover:text-gray-700 hover:bg-gray-100">
                  <Maximize size={16} />
                </button>
              </div>

              {/* 中间 - 设备选择和缩放 */}
              <div className="flex items-center gap-2">
                {/* 设备型号选择器 */}
                {deviceType !== "desktop" && (
                  <div className="relative">
                    <button
                      onClick={() => {
                        setShowDeviceDropdown(!showDeviceDropdown);
                      }}
                      className="flex items-center gap-1 px-3 h-7 rounded bg-gray-200 text-gray-700 hover:bg-gray-300 transition-colors"
                    >
                      <span className="text-xs">{selectedModel?.name}</span>
                      <ChevronDown size={14} />
                    </button>

                    {/* 设备选择下拉菜单 */}
                    {showDeviceDropdown && (
                      <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-1 w-56 bg-white border border-gray-200 rounded-lg shadow-lg z-10 py-1">
                        {/* 设备类型切换 */}
                        <div className="flex border-b border-gray-200 mx-1">
                          <button
                            onClick={() => {
                              setDeviceType("tablet");
                              setSelectedModel(deviceModels.tablet[0]);
                            }}
                            className={`flex-1 px-3 py-2 text-xs transition-colors ${
                              deviceType === "tablet" ? "bg-gray-100 text-gray-900" : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                            }`}
                          >
                            <Tablet size={14} className="inline mr-1" />
                            平板
                          </button>
                          <button
                            onClick={() => {
                              setDeviceType("mobile");
                              setSelectedModel(deviceModels.mobile[0]);
                            }}
                            className={`flex-1 px-3 py-2 text-xs transition-colors ${
                              deviceType === "mobile" ? "bg-gray-100 text-gray-900" : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                            }`}
                          >
                            <Smartphone size={14} className="inline mr-1" />
                            手机
                          </button>
                        </div>

                        {/* 设备型号列表 */}
                        <div className="max-h-48 overflow-y-auto">
                          {deviceModels[deviceType === "tablet" ? "tablet" : "mobile"].map((model) => (
                            <button
                              key={model.id}
                              onClick={() => {
                                setSelectedModel(model);
                                setShowDeviceDropdown(false);
                              }}
                              className={`w-full px-3 py-2 text-xs text-left transition-colors ${
                                selectedModel?.id === model.id ? "bg-blue-50 text-blue-600" : "text-gray-700 hover:bg-gray-50"
                              }`}
                            >
                              {model.name}
                              <span className="text-gray-400 ml-2">{model.width} × {model.height}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* 缩放控制 */}
                <div className="flex items-center gap-0.5 bg-gray-200 rounded px-1">
                  <button
                    onClick={() => setZoom(Math.max(25, zoom - 25))}
                    className="flex items-center justify-center w-6 h-6 rounded text-gray-500 hover:text-gray-700 hover:bg-gray-300"
                  >
                    <Minus size={14} />
                  </button>
                  <span className="text-xs text-gray-700 px-1 min-w-[40px] text-center">{zoom}%</span>
                  <button
                    onClick={() => setZoom(Math.min(200, zoom + 25))}
                    className="flex items-center justify-center w-6 h-6 rounded text-gray-500 hover:text-gray-700 hover:bg-gray-300"
                  >
                    <Plus size={14} />
                  </button>
                </div>
              </div>

              {/* 右侧 - 编辑按钮 */}
              <div className="flex items-center gap-1">
                <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded border border-gray-300 text-gray-600 bg-gray-200 hover:bg-gray-300 transition-colors">
                  <Edit3 size={14} />
                  编辑
                </button>
              </div>
            </div>

            {/* 预览内容区域 */}
            <div className="flex-1 overflow-hidden bg-gray-100 flex items-center justify-center p-4">
              {effectivePreviewSource.mode === "none" ? (
                <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                  暂无预览内容
                </div>
              ) : deviceType === "desktop" ? (
                <div className="w-full h-full bg-white rounded-lg overflow-hidden shadow-lg">
                  {effectivePreviewSource.mode === "html" ? (
                    <iframe
                      srcDoc={effectivePreviewSource.html}
                      sandbox="allow-scripts"
                      className="w-full h-full border-0"
                      title="页面预览"
                    />
                  ) : (
                    <iframe
                      src={effectivePreviewSource.url}
                      className="w-full h-full border-0"
                      title="应用预览"
                    />
                  )}
                </div>
              ) : (
                <div
                  className="shadow-lg"
                  style={{
                    width: `${selectedModel?.width}px`,
                    height: `${selectedModel?.height}px`,
                    transform: `scale(${zoom / 100})`,
                    transformOrigin: "center center",
                  }}
                >
                  <div className="w-full h-full bg-white rounded-lg overflow-hidden border border-gray-200">
                    {effectivePreviewSource.mode === "html" ? (
                      <iframe
                        srcDoc={effectivePreviewSource.html}
                        sandbox="allow-scripts"
                        className="w-full h-full border-0"
                        title="页面预览"
                      />
                    ) : (
                      <iframe
                        src={effectivePreviewSource.url}
                        className="w-full h-full border-0"
                        title="应用预览"
                      />
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 代码 Tab */}
        {activeTab === "code" && (
          <CodePanel
            files={fileTree}
            selectedFile={selectedFile}
            onSelect={handleFileSelect}
            fileContent={fileContent}
            isLoading={isLoading}
          />
        )}
      </div>
    </div>
  );
}
