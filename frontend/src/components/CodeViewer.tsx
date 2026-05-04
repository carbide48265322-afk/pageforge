import { useState, useEffect, useRef, type ReactNode } from "react";

/**
 * 文件内容和语言信息
 */
export interface FileContent {
  path: string;
  content: string;
  language: string;
}

/** CodeViewer 组件的 props */
interface CodeViewerProps {
  file?: FileContent;
  isLoading?: boolean;
}

/**
 * 根据文件路径获取 Monaco 语言 ID
 */
function getMonacoLanguage(path: string): string {
  const ext = path.split(".").pop()?.toLowerCase();
  const langMap: Record<string, string> = {
    ts: "typescript",
    tsx: "typescript",
    js: "javascript",
    jsx: "javascript",
    css: "css",
    scss: "scss",
    less: "less",
    html: "html",
    json: "json",
    md: "markdown",
    py: "python",
    java: "java",
    cpp: "cpp",
    c: "c",
    rs: "rust",
    go: "go",
  };
  return langMap[ext || ""] || "plaintext";
}

/**
 * Monaco Editor 懒加载组件
 * 首次挂载时才动态加载 monaco-editor（约 3MB）
 */
function MonacoEditor({
  content,
  language,
  path,
}: {
  content: string;
  language: string;
  path: string;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const editorRef = useRef<any>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadMonaco() {
      // 动态导入 monaco-editor（懒加载）
      const monaco = await import("monaco-editor");

      if (cancelled) return;

      if (containerRef.current && !editorRef.current) {
        editorRef.current = monaco.editor.create(containerRef.current, {
          value: content,
          language: language,
          theme: "vs-dark",
          readOnly: true,  // 只读模式
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          automaticLayout: true,
          fontSize: 14,
          wordWrap: "on",
          lineNumbers: "on",
          renderLineHighlight: "all",
        });
      } else if (editorRef.current) {
        // 更新内容和语言
        editorRef.current.setValue(content);
        const model = editorRef.current.getModel();
        if (model) {
          monaco.editor.setModelLanguage(model, language);
        }
      }
    }

    loadMonaco();

    return () => {
      cancelled = true;
    };
  }, [content, language]);

  // 组件卸载时销毁编辑器
  useEffect(() => {
    return () => {
      if (editorRef.current) {
        editorRef.current.dispose();
        editorRef.current = null;
      }
    };
  }, []);

  return <div ref={containerRef} className="h-full w-full" />;
}

/**
 * 代码查看器组件
 * 使用 Monaco Editor 实现语法高亮
 * 懒加载：组件挂载时才加载 Monaco（3MB）
 */
export function CodeViewer({ file, isLoading }: CodeViewerProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400 text-sm">
        <span className="animate-spin mr-2">⟳</span>
        加载中...
      </div>
    );
  }

  if (!file) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400 text-sm">
        请选择文件
      </div>
    );
  }

  const language = getMonacoLanguage(file.path);

  return (
    <div className="h-full flex flex-col">
      {/* 文件路径面包屑 */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-700 bg-gray-800 text-gray-300 text-xs">
        <span className="text-gray-500">📄</span>
        <span className="truncate">{file.path}</span>
        <span className="ml-auto text-gray-500">{language}</span>
      </div>

      {/* Monaco Editor */}
      <div className="flex-1 overflow-hidden">
        <MonacoEditor
          content={file.content}
          language={language}
          path={file.path}
        />
      </div>
    </div>
  );
}
