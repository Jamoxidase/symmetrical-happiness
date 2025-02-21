import { useState, useCallback } from 'react';
import { Message, TableData } from '../types';
import { parseMessageContent } from '../DataLink';
import { SpinningTrnaCursor } from '../SpinningTrnaCursor';
import { cn } from '@/lib/utils';
import { Copy, Check } from 'lucide-react';

interface MessageBubbleProps {
  message: Message;
  tableData: TableData;
  model?: string;
}

export function MessageBubble({ message, tableData, model }: MessageBubbleProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(message.content || '');
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy message:', err);
    }
  }, [message.content]);

  return (
    <div className="w-full ml-0 px-6 py-3 group">
      {/* Message label */}
      <div className="mb-1 text-[var(--text-tertiary)] text-xs uppercase tracking-wide">
        {message.role === 'user' ? 'You' : `Assistant${message.model ? ` (${message.model})` : ''}`}
      </div>

      {/* Message content */}
      <div className={cn(
        "font-['Times New Roman']",
        message.role === 'user' 
          ? "text-[26px] leading-[1.5] text-[var(--text-primary)]" 
          : "text-[20px] leading-[1.5] text-[var(--text-primary)]"
      )}>
        {message.role === 'assistant' ? (
          <div>
            {message.content && parseMessageContent(message.content, tableData, message.isStreaming)}
            {message.isStreaming && (
              <div className="inline-flex items-center ml-1" role="status" aria-label="Loading response">
                <SpinningTrnaCursor />
              </div>
            )}
          </div>
        ) : (
          message.content
        )}
      </div>

      {/* Message actions */}
      {message.role === 'assistant' && !message.isStreaming && (
        <div className="mt-2 flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          {model && (
            <div className="text-[var(--text-tertiary)] text-xs">
              {model}
            </div>
          )}
          <button
            onClick={handleCopy}
            className="flex items-center gap-2 px-2 py-1 text-[var(--text-secondary)] 
                     hover:text-[var(--text-primary)] text-sm transition-colors"
            aria-label={copied ? "Message copied" : "Copy message"}
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      )}

      {/* Subtle separator */}
      <div className="mt-4 border-t border-[var(--border-color)]" />
    </div>
  );
}