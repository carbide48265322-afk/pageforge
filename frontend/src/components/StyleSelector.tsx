

interface DesignStyle {
  id: string;
  name: string;
  description: string;
  preview: string;
}

interface StyleSelectorProps {
  styles: DesignStyle[];
  selectedStyle: string;
  onStyleSelect: (styleId: string) => void;
}

export function StyleSelector({ styles, selectedStyle, onStyleSelect }: StyleSelectorProps) {
  return (
    <div className="p-4">
      <h3 className="text-sm font-medium text-gray-700 mb-3">选择设计风格</h3>
      <div className="grid grid-cols-2 gap-3">
        {styles.map((style) => (
          <button
            key={style.id}
            onClick={() => onStyleSelect(style.id)}
            className={`p-4 border rounded-lg text-left transition-all ${
              selectedStyle === style.id
                ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
            }`}
          >
            <div className="text-sm font-medium text-gray-800">{style.name}</div>
            <div className="text-xs text-gray-500 mt-1">{style.description}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
