interface JsonEditorProps {
  value: string
  onChange: (value: string) => void
}

export default function JsonEditor({ value, onChange }: JsonEditorProps) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      spellCheck={false}
      style={{
        fontFamily: 'monospace',
        fontSize: '13px',
        width: '100%',
        height: '420px',
        padding: '8px',
        border: '1px solid #aab7b8',
        borderRadius: '2px',
        resize: 'vertical',
        boxSizing: 'border-box',
        lineHeight: '1.5',
      }}
    />
  )
}
