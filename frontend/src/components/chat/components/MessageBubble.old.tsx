import { useState, useCallback } from 'react';
import { Message, TableData } from '../types';
import { parseMessageContent } from '../DataLink';
import { SpinningTrnaCursor } from '../SpinningTrnaCursor';
import { cn } from '@/lib/utils';
import { 
  Beaker, 
  User, 
  ThumbsUp, 
  ThumbsDown, 
  Copy, 
  Check, 
  Share2,
  MoreHorizontal 
} from 'lucide-react';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/components/ui/tooltip';
import { Alert } from '@/components/ui/alert';

interface MessageBubbleProps {
  message: Message;
  tableData: TableData;
}

interface FeedbackState {
  helpful?: boolean;
  reason?: string;
  submitted: boolean;
}

export function MessageBubble({ message, tableData }: MessageBubbleProps) {
  const [feedback, setFeedback] = useState<FeedbackState>({ submitted: false });
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [copied, setCopied] = useState(false);
  const [showActions, setShowActions] = useState(false);

  const formatTimestamp = (timestamp: string): string => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: true
    });
  };

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(message.content || '');
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy message:', err);
    }
  }, [message.content]);

  const handleShare = useCallback(async () => {
    try {
      await navigator.share({
        title: 'tRNA Analysis Chat',
        text: message.content || '',
        url: window.location.href
      });
    } catch (err) {
      if (err instanceof Error && err.name !== 'AbortError') {
        console.error('Failed to share message:', err);
      }
    }
  }, [message.content]);

  const handleFeedback = useCallback((helpful: boolean) => {
    setFeedback(prev => ({ ...prev, helpful, submitted: true }));
    setShowFeedbackForm(true);
  }, []);

  const submitFeedback = useCallback((reason: string) => {
    setFeedback(prev => ({ ...prev, reason }));
    setShowFeedbackForm(false);
    // TODO: Send feedback to server
  }, []);

  return (
    <TooltipProvider>
      <div 
        className="flex flex-col gap-1 group animate-in slide-in-from-bottom-2"
        role={message.role === 'assistant' ? 'article' : 'complementary'}
      >
      {/* Message header */}
      <div className="flex items-center gap-2 text-sm text-gray-500 ml-2 mb-1">
        {message.role === 'user' ? (
          <>
            <User size={14} className="text-blue-400" />
            <span>User</span>
          </>
        ) : (
          <>
            <Beaker size={14} className="text-emerald-400" />
            <span>tRNA Analysis Agent</span>
          </>
        )}
        <span className="text-gray-600" aria-hidden="true">·</span>
        <time 
          dateTime={new Date(message.timestamp).toISOString()}
          className="text-xs"
        >
          {formatTimestamp(message.timestamp)}
        </time>
      </div>
      
      {/* Message content */}
      <div
        className={cn(
          "relative max-w-[85%] rounded-xl px-4 py-3 transition-colors",
          "hover:shadow-md hover:shadow-black/5",
          message.role === 'user'
            ? "bg-blue-600/20 border border-blue-500/20 text-gray-100 hover:bg-blue-600/25"
            : "bg-gray-800 border border-gray-700 text-gray-100 hover:bg-gray-800/80"
        )}
      >
        {/* Message actions */}
        {message.role === 'assistant' && !message.isStreaming && (
          <div className="absolute -right-12 top-2 flex flex-col gap-2">
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                onClick={handleCopy}
                className={cn(
                  "p-2 rounded-lg transition-all duration-200",
                  "opacity-0 group-hover:opacity-100",
                  "hover:bg-gray-700/50 focus:outline-none focus:ring-2 focus:ring-blue-500/50",
                  copied && "text-green-400"
                )}
                aria-label={copied ? "Message copied" : "Copy message"}
              >
                {copied ? <Check size={16} /> : <Copy size={16} />}
              </button>
            </Tooltip>

            {navigator.share && (
              <Tooltip content="Share message">
                <button
                  onClick={handleShare}
                  className={cn(
                    "p-2 rounded-lg opacity-0 group-hover:opacity-100",
                    "hover:bg-gray-700/50 transition-all duration-200",
                    "focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  )}
                  aria-label="Share message"
                >
                  <Share2 size={16} />
                </button>
              </Tooltip>
            )}

            <Tooltip content="More actions">
              <button
                onClick={() => setShowActions(!showActions)}
                className={cn(
                  "p-2 rounded-lg transition-all duration-200",
                  "opacity-0 group-hover:opacity-100",
                  "hover:bg-gray-700/50 focus:outline-none focus:ring-2 focus:ring-blue-500/50",
                  showActions && "bg-gray-700/50"
                )}
                aria-label="Show more actions"
                aria-expanded={showActions}
              >
                <MoreHorizontal size={16} />
              </button>
            </Tooltip>
          </div>
        )}

        {/* Message text */}
        <div 
          className="whitespace-pre-wrap break-words font-sans"
          role={message.role === 'assistant' ? 'article' : 'complementary'}
        >
          {message.role === 'assistant' ? (
            <>
              {message.content && parseMessageContent(message.content, tableData)}
              {message.isStreaming && (
                <div className="inline-flex items-center" role="status" aria-label="Loading response">
                  <span className="mr-2" />
                  <SpinningTrnaCursor />
                </div>
              )}
            </>
          ) : (
            message.content
          )}
        </div>

        {/* Feedback section */}
        {message.role === 'assistant' && !message.isStreaming && (
          <div className="mt-2 pt-2 border-t border-gray-700/50">
            {!feedback.submitted ? (
              <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                <Tooltip content="This was helpful">
                  <button
                    onClick={() => handleFeedback(true)}
                    className={cn(
                      "text-xs flex items-center gap-1 px-2 py-1 rounded",
                      "text-gray-400 hover:text-green-400",
                      "hover:bg-gray-700/50 transition-colors",
                      "focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                    )}
                    aria-label="Mark as helpful"
                  >
                    <ThumbsUp size={12} />
                    <span>Helpful</span>
                  </button>
                </Tooltip>
                <Tooltip content="This needs improvement">
                  <button
                    onClick={() => handleFeedback(false)}
                    className={cn(
                      "text-xs flex items-center gap-1 px-2 py-1 rounded",
                      "text-gray-400 hover:text-red-400",
                      "hover:bg-gray-700/50 transition-colors",
                      "focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                    )}
                    aria-label="Mark as needing improvement"
                  >
                    <ThumbsDown size={12} />
                    <span>Improve</span>
                  </button>
                </Tooltip>
              </div>
            ) : showFeedbackForm ? (
              <div className="mt-2 space-y-2">
                <textarea
                  placeholder={feedback.helpful 
                    ? "What was most helpful about this response?"
                    : "How could this response be improved?"}
                  className={cn(
                    "w-full px-3 py-2 text-sm rounded-md",
                    "bg-gray-900 border border-gray-700",
                    "text-gray-100 placeholder-gray-500",
                    "focus:outline-none focus:ring-2 focus:ring-blue-500/50",
                    "resize-none"
                  )}
                  rows={3}
                  onChange={(e) => submitFeedback(e.target.value)}
                />
                <div className="flex justify-end gap-2">
                  <button
                    onClick={() => setShowFeedbackForm(false)}
                    className="text-xs text-gray-400 hover:text-gray-300"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => submitFeedback('')}
                    className="text-xs text-blue-400 hover:text-blue-300"
                  >
                    Submit
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-xs text-gray-400">
                Thanks for your feedback!
              </div>
            )}
          </div>
        )}
      </div>
    </div>
    </TooltipProvider>
  );
}