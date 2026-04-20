import { useState } from 'react';

interface SchemaProperty {
  type: string;
  enum?: string[];
  title?: string;
  description?: string;
}

interface HumanInputSchema {
  type: string;
  title: string;
  properties: Record<string, SchemaProperty>;
  required?: string[];
}

interface HumanInputRequest {
  checkpoint_id: string;
  title: string;
  description: string;
  schema: HumanInputSchema;
  context: {
    prd?: string;
    design_concept?: string;
  };
}

interface HumanInputFormProps {
  request: HumanInputRequest;
  onSubmit: (data: { action: string; [key: string]: any }) => void;
}

export function HumanInputForm({ request, onSubmit }: HumanInputFormProps) {
  const [formData, setFormData] = useState<Record<string, any>>({});
  const schema = request.schema;

  const handleSubmit = (action: string) => {
    onSubmit({ ...formData, action });
  };

  const renderField = (key: string, property: SchemaProperty) => {
    if (property.enum) {
      return (
        <div key={key} className="field" style={{ marginBottom: '12px' }}>
          <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>
            {property.title || key}
          </label>
          <select
            value={formData[key] || ''}
            onChange={(e) => setFormData({ ...formData, [key]: e.target.value })}
            style={{
              width: '100%',
              padding: '8px 12px',
              borderRadius: '4px',
              border: '1px solid #d9d9d9',
              fontSize: '14px'
            }}
          >
            <option value="">请选择</option>
            {property.enum.map((opt) => (
              <option key={opt} value={opt}>
                {opt === 'confirm' ? '✓ 确认' : opt === 'revise' ? '✎ 修改' : opt}
              </option>
            ))}
          </select>
        </div>
      );
    }

    if (property.type === 'string') {
      return (
        <div key={key} className="field" style={{ marginBottom: '12px' }}>
          <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>
            {property.title || key}
          </label>
          <textarea
            value={formData[key] || ''}
            onChange={(e) => setFormData({ ...formData, [key]: e.target.value })}
            placeholder={property.description}
            rows={4}
            style={{
              width: '100%',
              padding: '8px 12px',
              borderRadius: '4px',
              border: '1px solid #d9d9d9',
              fontSize: '14px',
              resize: 'vertical'
            }}
          />
        </div>
      );
    }

    return null;
  };

  const actionValue = formData.action;

  return (
    <div 
      className="human-input-form"
      style={{
        background: '#f6f8fa',
        border: '1px solid #e1e4e8',
        borderRadius: '8px',
        padding: '16px',
        margin: '12px 0'
      }}
    >
      <h3 style={{ margin: '0 0 8px 0', fontSize: '16px', fontWeight: 600 }}>
        {schema.title || request.title}
      </h3>
      
      {request.description && (
        <p style={{ margin: '0 0 12px 0', color: '#586069', fontSize: '14px' }}>
          {request.description}
        </p>
      )}
      
      {request.context.prd && (
        <div 
          className="prd-preview"
          style={{
            background: '#fff',
            border: '1px solid #e1e4e8',
            borderRadius: '6px',
            padding: '12px',
            marginBottom: '16px',
            maxHeight: '200px',
            overflow: 'auto'
          }}
        >
          <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#24292e' }}>
            📄 需求文档预览
          </h4>
          <pre style={{ margin: 0, fontSize: '12px', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            {request.context.prd}
          </pre>
        </div>
      )}

      <form onSubmit={(e) => e.preventDefault()}>
        {Object.entries(schema.properties).map(([key, prop]) => 
          renderField(key, prop)
        )}
        
        <div className="actions" style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
          <button 
            type="button" 
            onClick={() => handleSubmit('confirm')}
            disabled={!actionValue}
            style={{
              flex: 1,
              padding: '8px 16px',
              borderRadius: '6px',
              border: 'none',
              background: actionValue === 'confirm' ? '#2ea44f' : '#94d3a2',
              color: '#fff',
              fontSize: '14px',
              fontWeight: 500,
              cursor: actionValue ? 'pointer' : 'not-allowed',
              opacity: actionValue ? 1 : 0.6
            }}
          >
            ✓ 确认通过
          </button>
          <button 
            type="button" 
            onClick={() => handleSubmit('revise')}
            style={{
              flex: 1,
              padding: '8px 16px',
              borderRadius: '6px',
              border: '1px solid #d9d9d9',
              background: '#fafbfc',
              color: '#24292e',
              fontSize: '14px',
              fontWeight: 500,
              cursor: 'pointer'
            }}
          >
            ✎ 需要修改
          </button>
        </div>
      </form>
    </div>
  );
}

export type { HumanInputRequest, HumanInputSchema };
