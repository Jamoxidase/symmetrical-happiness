import { useState, useCallback } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function useConnectionManager(authToken) {
  const [connectionState, setConnectionState] = useState({
    error: null
  });

  const sendMessageWithRetry = useCallback(async (message, chatId, token, onMessageCallback, setActiveChat, model) => {
    if (!token) {
      setConnectionState(prev => ({
        ...prev,
        error: 'Authentication required'
      }));
      return false;
    }

    try {
      let response;
      
      // For existing chat, send message to that chat
      if (chatId) {
        console.log('Sending message to existing chat:', chatId);
        response = await fetch(`${API_URL}/api/chat/${chatId}/message/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ 
            content: message,
            model: model
          })
        });
      } 
      // For new chat, create it first
      else {
        console.log('Creating new chat');
        const title = message.split(/\s+/).slice(0, 5).join(' ') + 
                     (message.split(/\s+/).length > 5 ? '...' : '');
                     
        response = await fetch(`${API_URL}/api/chat/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            title,
            content: message,
            model: model
          })
        });
      }

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText);
      }

      // Process SSE response for both new and existing chats
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                console.log('Parsed SSE data:', data);
                // Set active chat for new chat creation
                if (!chatId && data.type === 'start' && data.chat) {
                  setActiveChat({
                    id: data.chat.id,
                    title: data.chat.title
                  });
                }
                onMessageCallback(data);
              } catch (e) {
                console.error('Error parsing SSE data:', e);
                if (line.slice(6).trim()) {
                  onMessageCallback({ type: 'token', content: line.slice(6).trim() });
                }
              }
            }
          }
        }

        return true;
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      console.error('Message send error:', error);
      setConnectionState(prev => ({
        ...prev,
        error: error.message || 'Failed to send message'
      }));
      return false;
    }
  }, []);

  return {
    connectionState,
    sendMessageWithRetry
  };
}

export { useConnectionManager };