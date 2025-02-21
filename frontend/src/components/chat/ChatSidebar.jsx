import { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, Plus, MoreVertical, Edit2, Trash2, LogOut } from 'lucide-react';
import { useChat } from './ChatContext';
import { useAuth } from './AuthContext';

export function ChatSidebar({ isOpen, onToggle, userEmail, membershipTier }) {
  const { 
    chats = [], 
    activeChat, 
    setActiveChat, 
    createChat, 
    updateChatTitle, 
    deleteChat, 
    loadChats,
    pagination,
    isLoadingChats
  } = useChat();
  const { accessToken, logout } = useAuth();
  const [editingChatId, setEditingChatId] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [showMenuForChat, setShowMenuForChat] = useState(null);

  // Only load chats once when component mounts and when accessToken changes
  useEffect(() => {
    if (accessToken) {
      loadChats(accessToken, pagination.page);
    }
  }, [accessToken]); // Intentionally omitting loadChats and pagination to prevent infinite loops

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) {
      return date.toLocaleTimeString(undefined, { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      });
    } else if (days === 1) {
      return 'Yesterday';
    } else if (days < 7) {
      return date.toLocaleDateString(undefined, { weekday: 'short' });
    } else {
      return date.toLocaleDateString(undefined, { 
        month: 'short', 
        day: 'numeric' 
      });
    }
  };

  const handleNewChat = async () => {
    try {
      const newChat = await createChat(accessToken, 'New Chat');
      setActiveChat(newChat);
      onToggle(true);
    } catch (error) {
      console.error('Error creating new chat:', error);
    }
  };

  return (
    <div className={`fixed inset-y-0 left-0 transition-all duration-300 ease-in-out z-50 
                  ${isOpen ? 'w-[280px]' : 'w-[72px]'}`}
         onClick={(e) => e.stopPropagation()}>
      <div className="h-full flex flex-col bg-[var(--bg-surface)] border-r border-[var(--border-color)] sidebar">
        {/* Top Section */}
        <div className="p-4 flex justify-between items-center border-b border-[var(--border-color)]">
          {isOpen ? (
            <>
              <h2 className="text-xl font-medium text-[var(--text-primary)]">tRNA Analysis</h2>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onToggle(false);
                }}
                className="p-1.5 hover:bg-[var(--bg-hover)] rounded-[var(--radius-sm)]
                         text-[var(--text-secondary)] hover:text-[var(--text-primary)]
                         transition-colors"
                title="Collapse sidebar"
              >
                <ChevronLeft size={20} />
              </button>
            </>
          ) : (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onToggle(true);
              }}
              className="group relative p-1.5 hover:bg-[var(--bg-hover)] rounded-[var(--radius-sm)]
                       text-[var(--text-secondary)] hover:text-[var(--text-primary)]
                       transition-colors mx-auto"
              title="Expand sidebar"
            >
              <ChevronRight size={20} />
              <span className="absolute left-full ml-2 px-2 py-1 bg-[var(--bg-surface)] 
                           text-[var(--text-primary)] text-sm rounded-md border border-[var(--border-color)]
                           opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50">
                Expand sidebar
              </span>
            </button>
          )}
        </div>

        {/* New Chat Button - Consistent Position */}
        <div className="p-4">
          {isOpen ? (
            <button
              onClick={handleNewChat}
              className="w-full flex items-center gap-2 px-4 py-3 bg-[var(--accent-color)]
                       text-white rounded-[var(--radius-md)] hover:bg-[var(--accent-color)]/90
                       transition-colors font-medium"
            >
              <Plus size={20} />
              <span>New Chat</span>
            </button>
          ) : (
            <button
              onClick={handleNewChat}
              className="group relative w-full flex justify-center p-3 hover:bg-[var(--bg-hover)]
                       text-[var(--text-secondary)] hover:text-[var(--text-primary)]
                       rounded-[var(--radius-md)] transition-colors"
              title="Start new chat"
            >
              <Plus size={20} />
              <span className="absolute left-full ml-2 px-2 py-1 bg-[var(--bg-surface)] 
                           text-[var(--text-primary)] text-sm rounded-md border border-[var(--border-color)]
                           opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50">
                Start new chat
              </span>
            </button>
          )}
        </div>

        {/* Chat List */}
        <div className="flex-1 overflow-y-auto py-2 px-2 space-y-1 no-scrollbar flex flex-col">
          <div className="flex-1">
            {isOpen && chats.map(chat => (
            <div
              key={chat.id}
              className={`group relative rounded-[var(--radius-md)] transition-colors
                        ${activeChat?.id === chat.id ? 'bg-[var(--bg-hover)]' : 'hover:bg-[var(--bg-input)]'}`}
            >
              <button
                onClick={() => setActiveChat(chat)}
                className="w-full px-3 py-2 text-left flex items-start gap-2"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-start gap-2">
                    <span className={`truncate ${
                      activeChat?.id === chat.id ? 'text-[var(--text-primary)]' : 'text-[var(--text-secondary)]'
                    }`}>
                      {chat.title}
                    </span>
                    <span className="text-[var(--text-tertiary)] text-xs whitespace-nowrap">
                      {formatDate(chat.last_message_at || chat.created_at)}
                    </span>
                  </div>
                  {chat.preview && (
                    <span className="block text-[var(--text-tertiary)] text-xs mt-1 truncate">
                      {chat.preview}
                    </span>
                  )}
                </div>
              </button>
              
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowMenuForChat(showMenuForChat === chat.id ? null : chat.id);
                }}
                className={`absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-[var(--radius-sm)] 
                          transition-colors z-10 bg-[var(--bg-surface)]
                          ${showMenuForChat === chat.id 
                            ? 'bg-[var(--bg-hover)] text-[var(--text-primary)]' 
                            : 'text-[var(--text-tertiary)] opacity-0 group-hover:opacity-100'}`}
              >
                <MoreVertical size={16} />
              </button>

              {showMenuForChat === chat.id && (
                <div className="absolute right-0 top-8 w-48 py-1 bg-[var(--bg-input)] rounded-[var(--radius-md)]
                              border border-[var(--border-color)] shadow-lg z-50">
                  <button
                    onClick={() => {
                      setEditingChatId(chat.id);
                      setEditTitle(chat.title);
                      setShowMenuForChat(null);
                    }}
                    className="flex items-center gap-2 w-full px-3 py-2 text-sm text-[var(--text-secondary)]
                             hover:bg-[var(--bg-hover)] transition-colors"
                  >
                    <Edit2 size={16} />
                    Rename
                  </button>
                  <button
                    onClick={async () => {
                      try {
                        await deleteChat(accessToken, chat.id);
                        setShowMenuForChat(null); // Close the menu
                        // Force refresh the chat list
                        setTimeout(() => {
                          loadChats(accessToken);
                        }, 100); // Small delay to ensure the delete request completes
                      } catch (error) {
                        console.error('Error deleting chat:', error);
                      }
                    }}
                    className="flex items-center gap-2 w-full px-3 py-2 text-sm text-[var(--accent-color)]
                             hover:bg-[var(--bg-hover)] transition-colors"
                  >
                    <Trash2 size={16} />
                    Delete
                  </button>
                </div>
              )}
            </div>
          ))}
          </div>
          
          {/* Pagination */}
          {isOpen && pagination.total_pages > 1 && (
            <div className="mt-4 flex justify-center items-center gap-2 py-2 border-t border-[var(--border-color)]">
              {Array.from({ length: pagination.total_pages }, (_, i) => i + 1).map((pageNum) => (
                <button
                  key={pageNum}
                  onClick={() => loadChats(accessToken, pageNum)}
                  className={`w-8 h-8 flex items-center justify-center rounded-[var(--radius-sm)] 
                    border border-[var(--border-color)] transition-colors
                    ${pagination.page === pageNum 
                      ? 'bg-[var(--accent-color)] text-white border-[var(--accent-color)]' 
                      : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--accent-color)]'
                    }`}
                >
                  {pageNum}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* User Section - Consistent Position */}
        <div className="p-4 border-t border-[var(--border-color)] bg-[var(--bg-input)]">
          {isOpen ? (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-[var(--accent-color)]/20 
                            flex items-center justify-center text-[var(--accent-color)]
                            ring-1 ring-[var(--accent-color)]/30">
                  <span className="text-lg font-medium leading-none">
                    {userEmail[0].toUpperCase()}
                  </span>
                </div>
                <div>
                  <div className="font-medium text-[var(--text-primary)]">{membershipTier}</div>
                  <div className="text-sm text-[var(--text-secondary)]">{userEmail}</div>
                </div>
              </div>
              <button
                onClick={logout}
                className="group relative p-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)]
                         hover:bg-[var(--bg-hover)] rounded-[var(--radius-md)] transition-colors"
                title="Sign out"
              >
                <LogOut size={20} />
                <span className="absolute left-full ml-2 px-2 py-1 bg-[var(--bg-surface)] 
                             text-[var(--text-primary)] text-sm rounded-md border border-[var(--border-color)]
                             opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50">
                  Sign out
                </span>
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-[var(--accent-color)]/20 
                          flex items-center justify-center text-[var(--accent-color)]
                          ring-1 ring-[var(--accent-color)]/30">
                <span className="text-lg font-medium leading-none">
                  {userEmail[0].toUpperCase()}
                </span>
              </div>
              <button
                onClick={logout}
                className="group relative p-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)]
                         hover:bg-[var(--bg-hover)] rounded-[var(--radius-md)] transition-colors"
                title="Sign out"
              >
                <LogOut size={20} />
                <span className="absolute left-full ml-2 px-2 py-1 bg-[var(--bg-surface)] 
                             text-[var(--text-primary)] text-sm rounded-md border border-[var(--border-color)]
                             opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50">
                  Sign out
                </span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}