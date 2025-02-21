"""Secure database access module for chat history."""
import logging
from typing import List, Dict, Optional
from django.db import transaction
from django.core.exceptions import PermissionDenied
from asgiref.sync import sync_to_async
from .models import Chat, Message, Sequence

logger = logging.getLogger(__name__)

class ChatHistoryAccess:
    """Secure access to chat history data."""
    
    @staticmethod
    async def get_recent_chat_history(user_id: str, chat_id: str, message_limit: int = 6) -> List[Dict]:
        """Get recent chat history for a specific user and chat.
        
        Args:
            user_id: The ID of the user requesting history
            chat_id: The ID of the chat to get history from
            message_limit: Number of most recent messages to retrieve (default 6 for 3 pairs)
            
        Returns:
            List of recent messages with their associated sequences in chronological order
            
        Raises:
            PermissionDenied: If user doesn't have access to the chat
            ValueError: If parameters are invalid
        """
        try:
            # Verify chat exists and belongs to user
            chat = await sync_to_async(Chat.objects.filter(
                id=chat_id,
                user_id=user_id
            ).first)()
            
            if not chat:
                raise PermissionDenied("Chat not found or access denied")
            
            # Get recent messages with sequences
            logger.debug(f"Querying messages for chat_id: {chat_id} (type: {type(chat_id)})")
            try:
                # Convert string UUID to UUID object if needed
                from uuid import UUID
                chat_uuid = chat_id if isinstance(chat_id, UUID) else UUID(chat_id)
                
                messages = await sync_to_async(list)(
                    Message.objects.filter(chat_id=chat_uuid)
                    .order_by('-created_at')  # Newest first
                    .prefetch_related('sequences')
                    [:message_limit]  # Get last N messages
                )
                logger.debug(f"Found {len(messages)} messages")
                if not messages:
                    logger.debug("No messages found. Checking if chat exists...")
                    # Debug: Check if chat exists and has messages
                    chat_exists = await sync_to_async(Message.objects.filter(chat_id=chat_uuid).exists)()
                    logger.debug(f"Chat has any messages: {chat_exists}")
            except Exception as e:
                logger.error(f"Error querying messages: {str(e)}")
                raise
            
            # Reverse the list to get chronological order
            messages.reverse()
            
            logger.debug(f"Retrieved {len(messages)} messages from chat history")
            
            # Format messages with their sequences
            history = []
            for msg in messages:
                sequences = await sync_to_async(list)(msg.sequences.all())
                history.append({
                    'id': str(msg.id),
                    'role': msg.role,
                    'content': msg.content,
                    'created_at': msg.created_at.isoformat(),
                    'model': msg.model,  # Include the model
                    'sequences': [seq.to_dict() for seq in sequences] if sequences else []
                })
            
            return history  # Already in chronological order
            
        except Exception as e:
            logger.error(f"Error accessing chat history: {str(e)}")
            raise

    @staticmethod
    async def get_chat_context(user_id: str, chat_id: str) -> Optional[Dict]:
        """Get chat context including title and recent messages.
        
        Args:
            user_id: The ID of the user requesting context
            chat_id: The ID of the chat
            
        Returns:
            Dict containing chat info and recent messages, or None if not found
        """
        try:
            history = await ChatHistoryAccess.get_recent_chat_history(user_id, chat_id)
            chat = await sync_to_async(Chat.objects.filter(
                id=chat_id,
                user_id=user_id
            ).first)()
            
            if not chat:
                return None
                
            return {
                'chat': {
                    'id': str(chat.id),
                    'title': chat.title,
                    'created_at': chat.created_at.isoformat()
                },
                'recent_messages': history
            }
            
        except Exception as e:
            logger.error(f"Error getting chat context: {str(e)}")
            return None