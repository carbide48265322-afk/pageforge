

interface IdeationPanelProps {
  requirementsDoc: string;
  designConcept: string;
  onRequirementsChange: (doc: string) => void;
  onApprove: () => void;
  onRegenerate: () => void;
  isLoading: boolean;
}

export function IdeationPanel({
  requirementsDoc,
  designConcept,
  onRequirementsChange,
  onApprove,
  onRegenerate,
  isLoading
}: IdeationPanelProps) {
  return (
    <div className="flex flex-col h-full p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">构想阶段</h2>
        <div className="flex space-x-2">
          <button
            onClick={onRegenerate}
            disabled={isLoading}
            className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50"
          >
            重新生成
          </button>
          <button
            onClick={onApprove}
            disabled={isLoading}
            className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            确认需求
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto space-y-4">
        {/* 产品需求文档 */}
        <div className="bg-white border rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-2">产品需求文档</h3>
          <textarea
            value={requirementsDoc}
            onChange={(e) => onRequirementsChange(e.target.value)}
            className="w-full h-64 p-3 border rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="产品需求文档将在此显示..."
          />
        </div>

        {/* 设计概念 */}
        <div className="bg-white border rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-2">设计概念</h3>
          <div className="prose prose-sm max-w-none text-gray-600 whitespace-pre-wrap">
            {designConcept || '设计概念将在此显示...'}
          </div>
        </div>
      </div>
    </div>
  );
}
