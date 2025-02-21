import { useState, useRef, useEffect } from 'react';
import { flushSync } from 'react-dom';
import { Message, TableData, Chat } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface UseMessagesProps {
  activeChat: Chat | null;
  authToken: string | null;
}

interface UseMessagesReturn {
  messages: Message[];
  tableData: TableData;
  isLoading: boolean;
  setIsLoading: (value: boolean) => void;
  handleServerMessage: (data: string | Record<string, any>) => void;
}

export function useMessages({ activeChat, authToken }: UseMessagesProps): UseMessagesReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [tableData, setTableData] = useState<TableData>({});
  const [isLoading, setIsLoading] = useState(false);
  const streamingContentRef = useRef<string>('');

  // Track whether we're currently loading history
  const isLoadingHistory = useRef(false);
  const pendingMessages = useRef<Message[]>([]);

  // Track if we're in an active conversation
  const isActiveConversation = useRef(false);
  const lastChatId = useRef<string | null>(null);
  const isStreaming = useRef(false);

  // Load chat history when switching chats
  useEffect(() => {
    // Only consider it a chat switch if the ID actually changed
    if (activeChat?.id !== lastChatId.current) {
      console.log('Chat ID changed from', lastChatId.current, 'to', activeChat?.id);
      lastChatId.current = activeChat?.id || null;
      
      // Don't load history if we're streaming
      if (isStreaming.current) {
        console.log('Skipping history load - streaming in progress');
        return;
      }
      
      isActiveConversation.current = false;
    }

    if (activeChat?.id && authToken) {
      console.log('Loading chat history for:', activeChat.id);
      isLoadingHistory.current = true;
      
      const loadChatHistory = async () => {
        try {
          const response = await fetch(`${API_URL}/api/chat/${activeChat.id}/`, {
            headers: {
              'Authorization': `Bearer ${authToken}`
            }
          });
          const data = await response.json();

          if (data.messages) {
            // Don't load history if we started a conversation while loading
            if (isActiveConversation.current) {
              console.log('Discarding history - conversation started');
              return;
            }

            console.log('Setting messages from history:', data.messages);
            const historyMessages = data.messages.map(msg => {
              const content = msg.content || msg.user_content || '';
              console.log(`Processing message ${msg.id}:`, { role: msg.role, content });
              return {
                id: msg.id,
                role: msg.role,
                content,
                timestamp: msg.created_at,
                model: msg.model
              };
            });

            setMessages(historyMessages);
          }
        } catch (error) {
          console.error('Error loading chat history:', error);
        } finally {
          isLoadingHistory.current = false;
        }
      };
      loadChatHistory();
    } else if (!activeChat?.id) {
      console.log('Clearing messages - no active chat');
      setMessages([]);
      isActiveConversation.current = false;
      isLoadingHistory.current = false;
    }
  }, [activeChat?.id, authToken]);

  const handleServerMessage = (data: string | Record<string, any>) => {
    console.log('Received SSE message:', data);
    try {
      const parsedData = typeof data === 'string' ? JSON.parse(data) : data;
      console.log('Parsed message data:', parsedData);
      
      switch (parsedData.type) {
        case 'sequence_data':
          console.log('Received sequence data:', parsedData.data);
          if (!parsedData.data?.gene_symbol) {
            console.error('Missing gene_symbol in sequence data');
            break;
          }

          flushSync(() => {
            setTableData(prev => {
              const newData = {
                ...prev,
                sequences: {
                  ...(prev.sequences || {}),
                  [parsedData.data.gene_symbol]: parsedData.data
                }
              };
              console.log('Updated tableData:', newData);
              return newData;
            });
          });
          break;

        case 'start':
          // Chat started
          // Mark that we're in an active conversation and streaming
          isActiveConversation.current = true;
          isStreaming.current = true;
          
          // Create both user and assistant messages immediately
          streamingContentRef.current = '';
          const userMessageId = crypto.randomUUID();
          const assistantMessageId = crypto.randomUUID();
          
          const newMessages = [
            {
              id: userMessageId,
              role: 'user',
              content: parsedData.user_message || '',  // Use the actual user message
              timestamp: parsedData.timestamp
            },
            {
              id: assistantMessageId,
              role: 'assistant',
              content: '',  // Start empty
              timestamp: parsedData.timestamp,
              isStreaming: true,
              model: parsedData.model
            }
          ];

          console.log('Adding new messages:', newMessages);
          flushSync(() => {
            setMessages(prev => [...prev, ...newMessages]);
          });
          break;

        case 'token':
          console.log('Received token:', parsedData.content);
          if (typeof parsedData.content === 'string') {
            streamingContentRef.current += parsedData.content;
            
            flushSync(() => {
              setMessages(prev => {
                // Find the streaming message
                const hasStreaming = prev.some(msg => msg.isStreaming);
                if (!hasStreaming) {
                  console.warn('No streaming message found in token event');
                  return prev;
                }
                
                return prev.map(msg => 
                  msg.isStreaming
                  ? { 
                      ...msg,
                      content: streamingContentRef.current
                  }
                  : msg
                );
              });
            });
          } else {
            console.warn('Received non-string token:', parsedData.content);
          }
          break;

        case 'end':
          console.log('Chat ended, current messages:', messages);
          console.log('Final streaming content:', streamingContentRef.current);
          
          flushSync(() => {
            setMessages(prev => {
              console.log('Updating messages in end event, prev:', prev);
              const updated = prev.map(msg => {
                if (msg.isStreaming) {
                  console.log('Found streaming message:', msg);
                  return {
                    ...msg,
                    content: streamingContentRef.current,
                    isStreaming: false
                  };
                }
                return msg;
              });
              console.log('Updated messages:', updated);
              return updated;
            });
            setIsLoading(false);
          });
          
          // Keep conversation active but mark streaming as done
          isActiveConversation.current = true;
          isStreaming.current = false;
          
          // Don't clear streaming content immediately
          setTimeout(() => {
            streamingContentRef.current = '';
          }, 100);
          break;

        case 'error':
          console.warn('Server reported error:', parsedData.message);
          break;
      }
    } catch (error) {
      console.error('Error processing server message:', error);
    }
  };

  return {
    messages,
    setMessages,
    tableData,
    isLoading,
    setIsLoading,
    handleServerMessage
  };
}