import { createContext, useContext, useState, useCallback, useRef } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const ChatContext = createContext();

export function ChatProvider({ children }) {
  const [chats, setChats] = useState([]);
  const [activeChat, setActiveChat] = useState(null);
  const [currentModel, setCurrentModel] = useState(() => {
    // Try to get user's available models from localStorage
    const userStr = localStorage.getItem('chat_user');
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        if (user.available_models && user.available_models.length > 0) {
          return user.available_models[0];
        }
      } catch (e) {
        console.error('Error parsing user data:', e);
      }
    }
    return 'claude-3-5-sonnet';
  });
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 10,
    total_chats: 0,
    total_pages: 1
  });
  
  // Track if we're currently loading chats to prevent duplicate requests
  const [isLoadingChats, setIsLoadingChats] = useState(false);
  
  // Debounce timer ref to prevent rapid successive calls
  const debounceTimerRef = useRef(null);
  const lastLoadTimeRef = useRef(0);
  const MIN_INTERVAL = 2000; // Minimum time between loads in milliseconds

  const loadChats = useCallback(async (authToken, page = 1) => {
    // Clear any pending debounced calls
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Check if we're already loading or if it's too soon since last load
    const now = Date.now();
    if (isLoadingChats || (now - lastLoadTimeRef.current < MIN_INTERVAL)) {
      console.log('Skipping chat load - already loading or too frequent');
      return;
    }

    // Skip if we're already on the requested page and have chats loaded
    if (pagination.page === page && chats.length > 0) {
      return;
    }

    try {
      setIsLoadingChats(true);
      const response = await fetch(`${API_URL}/api/chat/?page=${page}&page_size=${pagination.page_size}`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      if (!response.ok) {
        // Don't update state if we can't connect - this prevents unnecessary re-renders
        if (response.status === 0) {
          console.error('Could not connect to server');
          return;
        }
        // If we get a 400 error about missing columns, just return empty list
        // This handles the case where the database isn't fully migrated
        setChats([]);
        setPagination(prev => ({ ...prev, total_chats: 0, total_pages: 1 }));
        return;
      }

      const data = await response.json();
      setChats(data.chats || []);
      setPagination(data.pagination || {
        page: 1,
        page_size: 10,
        total_chats: 0,
        total_pages: 1
      });
    } catch (error) {
      console.error('Error loading chats:', error);
      // Only update state if we have a real error, not a connection error
      if (error.name !== 'TypeError' || error.message !== 'Failed to fetch') {
        setChats([]);
        setPagination(prev => ({ ...prev, total_chats: 0, total_pages: 1 }));
      }
    } finally {
      setIsLoadingChats(false);
      lastLoadTimeRef.current = Date.now();
    }
  }, [isLoadingChats, MIN_INTERVAL, pagination.page_size]);
  
  const createChat = async (authToken, title, initialMessage) => {
    try {
      const response = await fetch(`${API_URL}/api/chat/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          title: title || 'New Chat',
          content: initialMessage,
          model: currentModel
        })
      });
      
      if (!response.ok) {
        // Handle connection errors differently
        if (response.status === 0) {
          throw new Error('Could not connect to server');
        }
        const errorText = await response.text();
        console.error('Failed to create chat:', errorText);
        throw new Error(errorText);
      }

      const data = await response.json();
      if (data.chat_id) {
        setActiveChat({
          id: data.chat_id,
          title: data.title || 'New Chat'
        });
        // Only load chats if we successfully created a new chat
        await loadChats(authToken);
      }
      return data;
    } catch (error) {
      console.error('Error creating chat:', error);
      // Don't try to load chats if we couldn't connect
      if (error.message !== 'Could not connect to server' && 
          error.name !== 'TypeError' && 
          error.message !== 'Failed to fetch') {
        await loadChats(authToken);
      }
      throw error;
    }
  };
  
  const sendMessage = async (authToken, chatId, content) => {
    try {
      const response = await fetch(`${API_URL}/api/chat/${chatId}/message/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content })
      });
      return response;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  };

  const updateChatTitle = async (authToken, chatId, title) => {
    try {
      const response = await fetch(`${API_URL}/api/chat/${chatId}/manage/`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title })
      });
      const data = await response.json();
      await loadChats(authToken);
      return data;
    } catch (error) {
      console.error('Error updating chat title:', error);
      throw error;
    }
  };

  const deleteChat = async (authToken, chatId) => {
    try {
      const response = await fetch(`${API_URL}/api/chat/${chatId}/manage/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      if (!response.ok) {
        throw new Error(`Failed to delete chat: ${response.status}`);
      }

      // Update local state immediately
      setChats(prevChats => prevChats.filter(chat => chat.id !== chatId));
      if (activeChat?.id === chatId) {
        setActiveChat(null);
      }
      
      // Refresh the chat list from server
      await loadChats(authToken);
    } catch (error) {
      console.error('Error deleting chat:', error);
      throw error;
    }
  };
  
  return (
    <ChatContext.Provider value={{
      chats,
      activeChat,
      setActiveChat,
      loadChats,
      createChat,
      sendMessage,
      updateChatTitle,
      deleteChat,
      pagination,
      isLoadingChats,
      currentModel,
      setCurrentModel
    }}>
      {children}
    </ChatContext.Provider>
  );
}

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};