import { useState } from 'react';
import { Download } from 'lucide-react';

interface ExportButtonProps {
  projectName: string;
  htmlContent: string;
  onExport: (projectName: string) => Promise<void>;
}

export function ExportButton({ projectName, htmlContent, onExport }: ExportButtonProps) {
  const [isExporting, setIsExporting] = useState(false);
  const [exportName, setExportName] = useState(projectName);

  const handleExport = async () => {
    if (!exportName.trim()) return;
    
    setIsExporting(true);
    try {
      await onExport(exportName);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="flex items-center space-x-2">
      <input
        type="text"
        value={exportName}
        onChange={(e) => setExportName(e.target.value)}
        placeholder="项目名称"
        className="px-3 py-1 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <button
        onClick={handleExport}
        disabled={isExporting || !htmlContent}
        className="flex items-center space-x-1 px-3 py-1 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Download size={16} />
        <span>{isExporting ? '导出中...' : '导出项目'}</span>
      </button>
    </div>
  );
}
