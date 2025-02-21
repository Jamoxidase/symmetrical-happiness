import { useState, useEffect, useRef } from 'react';
import { MoreHorizontal } from 'lucide-react';

interface ModelSelectorProps {
  models: string[];
  currentModel: string;
  onModelSelect: (model: string) => void;
  disabled?: boolean;
}

export function ModelSelector({ 
  models, 
  currentModel, 
  onModelSelect, 
  disabled 
}: ModelSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const selectorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectorRef.current && !selectorRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  return (
    <div className="relative" ref={selectorRef}>
      <button
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
        disabled={disabled}
        className="p-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] 
                   hover:bg-[var(--bg-hover)] rounded-[var(--radius-sm)] transition-colors"
        title="Select model"
      >
        <MoreHorizontal size={20} />
      </button>

      {isOpen && (
        <div className="absolute bottom-full mb-2 right-0 w-48 py-1 bg-[var(--bg-input)] 
                      rounded-[var(--radius-md)] border border-[var(--border-color)] shadow-lg z-50">
          {models.map(model => (
            <button
              key={model}
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onModelSelect(model);
                setIsOpen(false);
              }}
              type="button"
              className={`flex items-center w-full px-3 py-2 text-sm transition-colors
                ${currentModel === model 
                  ? 'text-[var(--accent-color)] bg-[var(--bg-hover)]'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'
                }`}
            >
              {model}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}