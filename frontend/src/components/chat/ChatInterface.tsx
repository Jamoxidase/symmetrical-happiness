import { useState, useRef, useCallback, useEffect } from 'react';
import { ChatSidebar } from './ChatSidebar';
import { useChat } from './ChatContext';
import ArtifactsPanel from './ArtifactsPanel';
import { useAuth } from './AuthContext';
import { useConnectionManager } from './ConnectionManager';
import { MessageList } from './components/MessageList';
import { ChatInput } from './components/ChatInput';
import { useMessages } from './hooks/useMessages';
import { Database } from 'lucide-react';

interface ErrorState {
  message: string;
  type: 'error' | 'warning' | 'info';
  id: number;
}

const ChatInterface: React.FC = () => {
  const { isAuthenticated, accessToken, user } = useAuth();
  const { activeChat, setActiveChat, currentModel, setCurrentModel } = useChat();
  const { connectionState, sendMessageWithRetry } = useConnectionManager(accessToken);

  const [input, setInput] = useState('');
  const [showSidebar, setShowSidebar] = useState(false);
  const [showArtifacts, setShowArtifacts] = useState(false);
  const [isOverlapping, setIsOverlapping] = useState(false);
  const [isDataViewerOverlapping, setIsDataViewerOverlapping] = useState(false);
  const [manualSidebarOverride, setManualSidebarOverride] = useState(false);
  const [errors, setErrors] = useState<ErrorState[]>([]);
  const [retryCount, setRetryCount] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const lastMessageRef = useRef<string>('');

  const {
    messages,
    tableData,
    isLoading,
    setIsLoading,
    handleServerMessage
  } = useMessages({ activeChat, authToken: accessToken });

  // Check for overlap conditions
  const checkOverlap = useCallback(() => {
    const windowWidth = window.innerWidth;
    const minChatWidth = 600;
    const expandedSidebarWidth = 280;
    const dataViewerWidth = 600;
    const buffer = 80;
    const collapseBuffer = 120;

    const availableWidth = windowWidth - buffer;
    const sidebarWidth = showSidebar ? expandedSidebarWidth : 72;
    
    // Check if expanded sidebar would overlap
    const wouldSidebarOverlap = availableWidth < minChatWidth + expandedSidebarWidth + collapseBuffer;
    setIsOverlapping(wouldSidebarOverlap);
    
    // Check if data viewer would overlap
    // Consider data viewer as overlapping if it would push chat area below optimal width
    const optimalChatWidth = 1000; // Desired width for chat area
    const wouldDataViewerOverlap = showArtifacts && 
      (availableWidth - sidebarWidth - buffer < optimalChatWidth + dataViewerWidth);
    setIsDataViewerOverlapping(wouldDataViewerOverlap);

    // Only auto-collapse on initial load or window resize, not on manual toggle
    if (wouldSidebarOverlap && !manualSidebarOverride) {
      setShowSidebar(false);
      setManualSidebarOverride(false);
    }
  }, [showArtifacts, manualSidebarOverride, showSidebar]);

  // Check overlap on mount and window resize
  useEffect(() => {
    checkOverlap();
    window.addEventListener('resize', checkOverlap);
    return () => window.removeEventListener('resize', checkOverlap);
  }, [checkOverlap]);

  // Check overlap when data viewer state changes
  useEffect(() => {
    checkOverlap();
  }, [showArtifacts, checkOverlap]);

  // Handle manual sidebar toggle
  const handleSidebarToggle = useCallback((newState: boolean) => {
    if (newState) {
      // When expanding, always allow it and set the override
      setShowSidebar(true);
      setManualSidebarOverride(true);
    } else {
      // When collapsing, remove the override
      setShowSidebar(false);
      setManualSidebarOverride(false);
    }
  }, []);

  const handleInteraction = useCallback((e: MouseEvent) => {
    const target = e.target as HTMLElement;
    const isDataViewerClick = target.closest('.data-viewer');
    const isSidebarClick = target.closest('.sidebar');
    const isMainContentClick = target.closest('.main-content');
    
    // Auto-collapse sidebar only if we're in overlapping state and clicking outside
    if (isOverlapping && !isSidebarClick && showSidebar) {
      setShowSidebar(false);
      setManualSidebarOverride(false);  // Reset override when auto-collapsing
    }

    // Only handle sidebar auto-collapse
  }, [isOverlapping, showSidebar, isDataViewerOverlapping, showArtifacts]);

  useEffect(() => {
    document.addEventListener('click', handleInteraction);
    return () => document.removeEventListener('click', handleInteraction);
  }, [handleInteraction]);

  // Show sidebar by default when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      setShowSidebar(true);
    }
  }, [isAuthenticated]);

  // Track if user is near bottom
  const [isNearBottom, setIsNearBottom] = useState(true);
  const messageContainerRef = useRef<HTMLDivElement>(null);

  const checkIfNearBottom = useCallback(() => {
    const container = messageContainerRef.current;
    if (!container) return;
    
    const threshold = 100; // pixels from bottom to consider "near bottom"
    const isNear = container.scrollHeight - container.scrollTop - container.clientHeight < threshold;
    setIsNearBottom(isNear);
  }, []);

  // Add scroll listener
  useEffect(() => {
    const container = messageContainerRef.current;
    if (!container) return;

    container.addEventListener('scroll', checkIfNearBottom);
    return () => container.removeEventListener('scroll', checkIfNearBottom);
  }, [checkIfNearBottom]);

  // Auto-scroll to bottom only if user was already near bottom
  useEffect(() => {
    if (isNearBottom) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isNearBottom]);

  const addError = useCallback((message: string, type: ErrorState['type'] = 'error') => {
    setErrors(prev => [...prev, { message, type, id: Date.now() }]);
  }, []);

  const removeError = useCallback((id: number) => {
    setErrors(prev => prev.filter(error => error.id !== id));
  }, []);

  useEffect(() => {
    const timeouts = errors.map(error => 
      setTimeout(() => removeError(error.id), 5000)
    );
    return () => timeouts.forEach(clearTimeout);
  }, [errors, removeError]);

  const sendMessage = async (messageText: string) => {
    if (!messageText.trim() || !isAuthenticated || isLoading) return;

    const trimmedMessage = messageText.trim();
    if (trimmedMessage === lastMessageRef.current && retryCount >= 3) {
      addError('Too many retries for the same message. Please try a different message.', 'warning');
      return;
    }

    setIsLoading(true);
    lastMessageRef.current = trimmedMessage;

    try {
      const wrappedHandler = (data: any) => {
        try {
          if (typeof data === 'string') {
            data = JSON.parse(data);
          }
          if (data.type === 'start') {
            data.user_message = trimmedMessage;
          } else if (data.type === 'error') {
            addError(data.message || 'An error occurred while processing your message.');
          }
          handleServerMessage(data);
        } catch (err) {
          console.error('Error handling server message:', err);
          addError('Failed to process server response.');
        }
      };

      const success = await sendMessageWithRetry(
        trimmedMessage,
        activeChat?.id,
        accessToken,
        wrappedHandler,
        setActiveChat,
        currentModel
      );
      
      if (!success) {
        setIsLoading(false);
        setRetryCount(prev => prev + 1);
        addError('Failed to send message. Please try again.');
      } else {
        setRetryCount(0);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setIsLoading(false);
      addError('Failed to send message: ' + (error instanceof Error ? error.message : 'Unknown error'));
    }
  };

  const handleSubmit = async (messageText) => {
    if (messageText.trim()) {
      await sendMessage(messageText);
    }
  };

  return (
    <div className="flex h-screen bg-[#1C1C1C] overflow-hidden">
      {/* Left Sidebar */}
      {isAuthenticated && (
        <ChatSidebar 
          isOpen={showSidebar} 
          onToggle={handleSidebarToggle}
          userEmail={user?.email || 'user@example.com'}
          membershipTier="Pro Member"
        />
      )}
      
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden pl-[72px]">
        <div className={`relative flex-1 flex flex-col items-center overflow-hidden
                      ${showSidebar ? 'ml-[208px]' : ''}`}>
          {/* Data Viewer Toggle */}
          <div className="absolute top-4 right-4 z-10">
            <button
              onClick={() => setShowArtifacts(!showArtifacts)}
              className="group relative p-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)]
                       bg-[var(--bg-surface)] hover:bg-[var(--bg-hover)] rounded-[var(--radius-md)] 
                       transition-colors border border-[var(--border-color)]"
              title={showArtifacts ? "Hide data viewer" : "Show data viewer"}
            >
              <Database size={20} />
              <span className="absolute right-full mr-2 px-2 py-1 bg-[var(--bg-surface)] 
                           text-[var(--text-primary)] text-sm rounded-md border border-[var(--border-color)]
                           opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50">
                {showArtifacts ? "Hide data viewer" : "Show data viewer"}
              </span>
            </button>
          </div>

          {/* Chat Container */}
          <div className={`w-full h-full flex flex-col overflow-hidden py-6 main-content transition-all duration-300
                        ${showArtifacts 
                          ? 'max-w-[calc(100%-640px)] mr-[600px]' 
                          : 'max-w-[1200px] mx-auto'}`}>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto" ref={messageContainerRef}>
              <MessageList
                messages={messages}
                tableData={tableData}
                isLoading={isLoading}
                isAuthenticated={isAuthenticated}
                onDemoSelect={sendMessage}
                connectionState={connectionState}
                messagesEndRef={messagesEndRef}
                availableModels={user?.available_models || []}
                currentModel={currentModel}
                onModelSelect={setCurrentModel}
              />
            </div>

            {/* Chat Input */}
            {messages.length > 0 && (
              <ChatInput
                input={input}
                setInput={setInput}
                onSubmit={handleSubmit}
                isLoading={isLoading}
                isAuthenticated={isAuthenticated}
                showArtifacts={showArtifacts}
                retryCount={retryCount}
                availableModels={user?.available_models || []}
                currentModel={currentModel}
                onModelSelect={setCurrentModel}
              />
            )}
          </div>
        </div>
      </div>

      {/* Right Data Viewer Panel */}
      <div className={`fixed top-0 right-0 bottom-0 w-[600px] border-l border-[var(--border-color)] 
                    bg-[#1C1C1C] shadow-lg transition-all duration-300 ease-in-out transform
                    data-viewer ${showArtifacts ? 'translate-x-0' : 'translate-x-full'}`}
                    style={{ backgroundColor: 'rgb(28, 28, 28)' }}>
        <ArtifactsPanel
          tableData={tableData}
          isOpen={showArtifacts}
          onClose={() => setShowArtifacts(false)}
        />
      </div>
    </div>
  );
};

export default ChatInterface;