import { DemoMessages } from '../DemoMessages';
import { Message, TableData, ConnectionState } from '../types';
import { Loader2, Send } from 'lucide-react';
import { MessageBubble } from './MessageBubble';
import { cn } from '@/lib/utils';
import { ModelSelector } from './ModelSelector';

interface MessageListProps {
  messages: Message[];
  tableData: TableData;
  isLoading: boolean;
  isAuthenticated: boolean;
  onDemoSelect: (message: string) => Promise<void>;
  connectionState: ConnectionState;
  messagesEndRef: React.RefObject<HTMLDivElement>;
  availableModels: string[];
  currentModel: string;
  onModelSelect: (model: string) => void;
}

export function MessageList({ 
  messages, 
  tableData, 
  isLoading, 
  isAuthenticated,
  onDemoSelect,
  connectionState,
  messagesEndRef,
  availableModels,
  currentModel,
  onModelSelect
}: MessageListProps) {
  return (
    <main 
      className="flex-1 overflow-y-auto scroll-smooth h-full"
      role="log"
      aria-label="Chat messages"
      aria-live="polite"
    >
      <div className="flex flex-col h-full">
        {messages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center px-4 py-12">
            {/* Welcome Text */}
            <div className="max-w-[800px] w-full space-y-4 mb-12">
              <h1 className="text-[32px] text-center text-white font-['Times New Roman']">
                Welcome to tRNA Analysis
              </h1>
              <p className="text-[#999999] text-center text-lg font-['Times New Roman']">
                I'm your research assistant for exploring tRNA data. I can help you analyze sequences,
                find patterns, and understand tRNA biology.
              </p>
            </div>

            {/* Input Box */}
            <div className="max-w-[800px] w-full mb-12">
              <div className="relative w-full bg-[#1E1E1E]/80 backdrop-blur-sm rounded-2xl border border-[#333333]/80 p-4">
                <div className="flex gap-4">
                  <div className="flex-1">
                    <textarea
                      placeholder="Ask a question about tRNA data..."
                      disabled={!isAuthenticated || isLoading}
                      className="w-full bg-transparent border-0 text-[20px] font-['Times New Roman'] text-white 
                               placeholder-[#666666] focus:outline-none focus:ring-0 resize-none leading-[1.6] 
                               tracking-[-0.01em] min-h-[56px]"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          const text = e.currentTarget.value.trim();
                          if (text) {
                            onDemoSelect(text);
                            e.currentTarget.value = '';
                          }
                        }
                      }}
                      aria-label={`New message input with ${currentModel} model`}
                    />
                  </div>
                  <div className="flex flex-col gap-2">
                    <button
                      disabled={!isAuthenticated || isLoading}
                      onClick={(e) => {
                        e.preventDefault();
                        const textarea = e.currentTarget.closest('.flex')?.querySelector('textarea');
                        if (textarea) {
                          const text = textarea.value.trim();
                          if (text) {
                            onDemoSelect(text);
                            textarea.value = '';
                          }
                        }
                      }}
                      className={cn(
                        "p-2 rounded-xl transition-all duration-300",
                        "flex items-center justify-center",
                        !isAuthenticated || isLoading
                          ? "text-[#6E6E73] cursor-not-allowed"
                          : "text-[var(--accent-color)] hover:text-[var(--accent-color)]/90"
                      )}
                    >
                      <Send className="h-6 w-6" />
                    </button>
                    <ModelSelector
                      models={availableModels}
                      currentModel={currentModel}
                      onModelSelect={onModelSelect}
                      disabled={isLoading || !isAuthenticated}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Example Questions */}
            <div className="max-w-[800px] w-full">
              <h2 className="text-[20px] text-center text-[#999999] font-['Times New Roman'] mb-6">
                Try These Examples
              </h2>
              <DemoMessages 
                onSelectDemo={onDemoSelect}
                disabled={!isAuthenticated || isLoading}
              />
            </div>
          </div>
        ) : (
          <div className="space-y-1">
            {messages.map((message, idx) => (
              <MessageBubble
                key={message.id || idx}
                message={message}
                tableData={tableData}
              />
            ))}
          </div>
        )}

        {/* Loading indicator */}
        {isLoading && ( 
          <div 
            className={cn(
              "flex items-center gap-3 px-4 py-3 w-full max-w-[800px] ml-0",
              "animate-pulse"
            )}
            role="status"
            aria-label="Processing your request"
          >
            <Loader2 className="h-5 w-5 text-[#0A84FF] animate-spin" />
            <span className="text-[#999999] text-lg font-['Times New Roman']">Processing query...</span>
          </div>
        )}

        <div ref={messagesEndRef} className="h-4" aria-hidden="true" />
      </div>
    </main>
  );
}