import { useState, useRef, useCallback } from 'react';
import { Send, Sparkles, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ModelSelector } from './ModelSelector';

interface ChatInputProps {
  input: string;
  setInput: (value: string) => void;
  onSubmit: (message: string) => Promise<void>;
  isLoading: boolean;
  isAuthenticated: boolean;
  showArtifacts: boolean;
  retryCount?: number;
  availableModels: string[];
  currentModel: string;
  onModelSelect: (model: string) => void;
}

const MAX_MESSAGE_LENGTH = 2000;

export function ChatInput({
  input,
  setInput,
  onSubmit,
  isLoading,
  isAuthenticated,
  showArtifacts,
  retryCount = 0,
  availableModels,
  currentModel,
  onModelSelect
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [error, setError] = useState<string | null>(null);

  const validateInput = useCallback((text: string) => {
    if (!text.trim()) {
      setError('Message cannot be empty');
      return false;
    }
    if (text.length > MAX_MESSAGE_LENGTH) {
      setError(`Message is too long (max ${MAX_MESSAGE_LENGTH} characters)`);
      return false;
    }
    if (retryCount > 3) {
      setError('Too many retries. Please try a different message.');
      return false;
    }
    return true;
  }, [retryCount]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!validateInput(input)) return;

    try {
      await onSubmit(input);
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = '56px';
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
    }
  };

  return (
    <div className="w-full px-6 mb-6">
      <form
        onSubmit={handleSubmit}
        className="relative flex gap-3 bg-[var(--bg-input)]/95 rounded-[var(--radius-lg)] shadow-lg 
                  border border-[var(--border-color)] p-4 backdrop-blur-sm backdrop-saturate-150
                  hover:border-[var(--border-color-hover)] hover:bg-[var(--bg-input)]/98 
                  transition-all duration-200"
      >
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              e.target.style.height = 'auto';
              e.target.style.height = e.target.scrollHeight + 'px';
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            className={cn(
              "w-full bg-transparent border-0 p-0",
              "text-white placeholder-[#666666] text-[20px] font-['Times New Roman']",
              "focus:outline-none focus:ring-0",
              "min-h-[24px] max-h-[200px]",
              "resize-none overflow-hidden leading-[1.6] tracking-[-0.01em]",
              (isLoading || !isAuthenticated) && "opacity-50 cursor-not-allowed"
            )}
            style={{
              height: 'auto',
            }}
            placeholder={
              !isAuthenticated
                ? "Please authenticate first..."
                : isLoading
                  ? "Processing..."
                  : "Ask a question about tRNA data..."
            }
            disabled={isLoading || !isAuthenticated}
            aria-invalid={!!error}
          />
        </div>

        <div className="flex flex-col gap-2">
          <button
            type="submit"
            disabled={!input.trim() || isLoading || !isAuthenticated}
            className={cn(
              "p-2 rounded-xl transition-all duration-300",
              "flex items-center justify-center",
              !input.trim() || isLoading || !isAuthenticated
                ? "text-[#6E6E73] cursor-not-allowed"
                : "text-[var(--accent-color)] hover:text-[var(--accent-color)]/90"
            )}
            title={
              !isAuthenticated
                ? "Please authenticate first"
                : isLoading
                  ? "Processing..."
                  : "Send message (Enter)"
            }
          >
            {isLoading ? (
              <Loader2 className="h-6 w-6 animate-spin" />
            ) : (
              <Send className="h-6 w-6" />
            )}
          </button>
          <ModelSelector
            models={availableModels}
            currentModel={currentModel}
            onModelSelect={onModelSelect}
            disabled={isLoading || !isAuthenticated}
          />
        </div>
      </form>

      {error && (
        <div className="absolute -top-12 left-0 right-0 text-[#EF4444] text-sm px-4">
          {error}
        </div>
      )}
    </div>
  );
}