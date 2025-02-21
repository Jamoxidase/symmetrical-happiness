import json
import jwt
import logging
import traceback
from typing import AsyncGenerator
from django.http import JsonResponse, StreamingHttpResponse
from django.views.generic.base import View
from django.core.exceptions import ValidationError
from asgiref.sync import sync_to_async
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from django.conf import settings

from .models import Chat, Message
from authentication.models import User
from .chatbot import ChatManager

logger = logging.getLogger(__name__)

async def get_user_from_token(request):
    """Validate and get user from authorization token"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise ValidationError('Invalid authorization header')
    
    token = auth_header[7:]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = payload['user_id']
        return await sync_to_async(User.objects.get)(id=user_id)
    except (jwt.InvalidTokenError, User.DoesNotExist) as e:
        raise ValidationError('Invalid token')

@method_decorator(csrf_exempt, name='dispatch')
class ChatView(View):
    """Handle chat listing and creation"""
    async def get(self, request):
        try:
            user = await get_user_from_token(request)
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            
            # Get total count
            total_chats = await sync_to_async(
                Chat.objects.filter(user=user, is_active=True).count
            )()
            
            # Get paginated chats
            offset = (page - 1) * page_size
            chats_qs = Chat.objects.filter(user=user, is_active=True).order_by('-created_at')[offset:offset + page_size]
            chats = await sync_to_async(lambda: list(chats_qs))()
            
            return JsonResponse({
                'chats': [{
                    'id': str(chat.id),
                    'title': chat.title,
                    'created_at': chat.created_at.isoformat(),
                    'last_message_at': chat.last_message_at.isoformat() if chat.last_message_at else None,
                    'model': chat.model  # Include model in chat list
                } for chat in chats],
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_chats': total_chats,
                    'total_pages': (total_chats + page_size - 1) // page_size
                }
            })
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=401)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=500)
        except BaseException as e:  # Catches ALL exceptions, including KeyboardInterrupt, SystemExit
            logger.critical(f"Critical error: {str(e)}")
            logger.critical(traceback.format_exc())
            return JsonResponse({'error (BaseException)': str(e)}, status=500)
    async def post(self, request):
        try:
            chat_manager = ChatManager()

            logger.debug("Received POST to /api/chat/")
            logger.debug(f"Headers: {dict(request.headers)}")
            logger.debug(f"Body: {request.body.decode('utf-8')}")
            
            user = await get_user_from_token(request)
            data = json.loads(request.body)
            
            content = data.get('content', '').strip()
            model = data.get('model', settings.DEFAULT_CHAT_MODEL)  # Use default model if not specified
            
            # Create title from content or default
            if 'title' in data:
                title = data['title']
            elif content:
                title = ' '.join(content.split()[:5]) + ('...' if len(content.split()) > 5 else '')
            else:
                title = 'New Chat'
            
            # Create chat
            chat = await sync_to_async(Chat.objects.create)(
                user=user,
                title=title,
                last_message_at=datetime.utcnow(),
                model=model
            )
            
            if not content:
                return JsonResponse({
                    'chat_id': str(chat.id),
                    'title': chat.title,
                    'model': model  # Include model in response
                })

            # Create first message - wouldnt it be so nice if we also added response in views
            message = await sync_to_async(Message.objects.create)(
                chat=chat,
                content=content,
                role='user',
                model=model  # Include model in message
            )

            # Get processor and set context
            processor = chat_manager.get_processor(str(user.id)) # makes a new processor
            processor.chat_id = str(chat.id)
            processor.message_id = str(message.id)

            async def event_stream() -> AsyncGenerator[bytes, None]:
                try:
                    start_event = {
                        'type': 'start',
                        'chat': {
                            'id': str(chat.id),
                            'title': chat.title,
                            'model': model  # Include model in start event
                        },
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    yield f"data: {json.dumps(start_event)}\n\n".encode('utf-8')
                    
                    async for chunk in processor.process_message(content):
                        chunk_data = f"data: {chunk}\n\n".encode('utf-8')
                        yield chunk_data
                        await sync_to_async(response.flush)()
                    
                    end_event = {
                        'type': 'end',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    yield f"data: {json.dumps(end_event)}\n\n".encode('utf-8')
                    
                except Exception as e:
                    logger.error(f"Error in event stream: {str(e)}")
                    logger.error(traceback.format_exc())
                    error_event = {
                        'type': 'error',
                        'error': str(e),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    yield f"data: {json.dumps(error_event)}\n\n".encode('utf-8')

            response = StreamingHttpResponse(
                streaming_content=event_stream(),
                content_type='text/event-stream'
            )
            response['Cache-Control'] = 'no-cache'
            response['X-Accel-Buffering'] = 'no'
            return response
            
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=401)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=500)
        except BaseException as e:  # Catches ALL exceptions, including KeyboardInterrupt, SystemExit
            logger.critical(f"Critical error: {str(e)}")
            logger.critical(traceback.format_exc())
            return JsonResponse({'error (BaseException)': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ChatHistoryView(View):
    """Handle retrieving chat history"""
    async def get(self, request, chat_id):
        try:
            page = int(request.GET.get('page', 1))
            page_size = min(int(request.GET.get('page_size', 50)), 100)
            
            user = await get_user_from_token(request)
            chat = await sync_to_async(Chat.objects.get)(id=chat_id, user=user)
            
            total_messages = await sync_to_async(Message.objects.filter(chat=chat).count)()
            
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            
            messages = await sync_to_async(lambda: list(
                Message.objects.filter(chat=chat)
                .order_by('created_at')
                [start_idx:end_idx]
            ))()
            
            # Get sequences for messages if they exist
            sequences = {}
            for msg in messages:
                get_sequences = lambda m=msg: list(m.sequences.all())
                msg_sequences = await sync_to_async(get_sequences)()
                if msg_sequences:
                    sequences[str(msg.id)] = [seq.to_dict() for seq in msg_sequences]
            
            return JsonResponse({
                'chat': {
                    'id': str(chat.id),
                    'title': chat.title,
                    'created_at': chat.created_at.isoformat(),
                    'model': chat.model  # Include model in chat info
                },
                'messages': [{
                    'id': str(msg.id),
                    'role': msg.role,
                    'content': msg.content,
                    'created_at': msg.created_at.isoformat(),
                    'sequences': sequences.get(str(msg.id), []),
                    'model': chat.model if msg.role == 'assistant' else None  # Include model in messages
                } for msg in messages],
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_messages': total_messages,
                    'total_pages': (total_messages + page_size - 1) // page_size
                }
            })
        except (Chat.DoesNotExist, ValidationError) as e:
            return JsonResponse({'error': str(e)}, status=401)
        except ValueError as e:
            return JsonResponse({'error': f'Invalid pagination parameters: {str(e)}'}, status=400)
        except Exception as e:
            logger.error(f"Error loading chat history: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ChatManagementView(View):
    """Handle chat updates and deletion"""
    async def put(self, request, chat_id):
        try:
            user = await get_user_from_token(request)
            data = json.loads(request.body)
            
            chat = await sync_to_async(Chat.objects.get)(id=chat_id, user=user, is_active=True)
            
            if 'title' in data:
                chat.title = data['title']
                await sync_to_async(chat.save)()
            
            return JsonResponse({
                'id': str(chat.id),
                'title': chat.title,
                'created_at': chat.created_at.isoformat(),
                'last_message_at': chat.last_message_at.isoformat() if chat.last_message_at else None,
                'model': chat.model  # Include model in response
            })
            
        except Chat.DoesNotExist:
            return JsonResponse({'error': 'Chat not found or access denied'}, status=404)
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=401)
        except Exception as e:
            logger.error(f"Error updating chat: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=500)
    
    async def delete(self, request, chat_id):
        try:
            user = await get_user_from_token(request)
            chat = await sync_to_async(Chat.objects.get)(id=chat_id, user=user, is_active=True)
            chat.is_active = False
            await sync_to_async(chat.save)()
            return JsonResponse({'status': 'success'})
            
        except Chat.DoesNotExist:
            return JsonResponse({'error': 'Chat not found or access denied'}, status=404)
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=401)
        except Exception as e:
            logger.error(f"Error deleting chat: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ChatMessageView(View):
    async def post(self, request, chat_id):
        """Process a new chat message"""
        try:

            logger.debug(f"Received POST to /api/chat/{chat_id}/message/")
            logger.debug(f"Headers: {dict(request.headers)}")
            logger.debug(f"Body: {request.body.decode('utf-8')}")
            
            chat_manager = ChatManager()
            
            # Validate user and get request data
            user = await get_user_from_token(request)
            data = json.loads(request.body)
            content = data.get('content')
            
            if not content:
                return JsonResponse({'error': 'Message content is required'}, status=400)
            
            # Get and validate chat
            chat = await sync_to_async(Chat.objects.get)(id=chat_id, user=user, is_active=True)
            
            # Use existing model or default
            model = data.get('model', chat.model or settings.DEFAULT_CHAT_MODEL)
            
            # Update chat model and last_message_at
            chat.model = model
            chat.last_message_at = datetime.utcnow()
            await sync_to_async(chat.save)(update_fields=['model', 'last_message_at'])
            
            # Create user message in database
            message = await sync_to_async(Message.objects.create)(
                chat=chat,
                content=content,
                role='user',
                model=model  # Include model in message
            )
            
            # Get processor and set context
            processor = chat_manager.get_processor(str(user.id))
            processor.chat_id = str(chat.id)
            processor.message_id = str(message.id)
            
            async def event_stream() -> AsyncGenerator[bytes, None]:
                try:
                    start_event = {
                        'type': 'start',
                        'chat': {
                            'id': str(chat.id),
                            'title': chat.title,
                            'model': model  # Include model in start event
                        },
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    yield f"data: {json.dumps(start_event)}\n\n".encode('utf-8')
                    
                    async for chunk in processor.process_message(content):
                        chunk_data = f"data: {chunk}\n\n".encode('utf-8')
                        yield chunk_data
                        await sync_to_async(response.flush)()
                    
                    end_event = {
                        'type': 'end',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    yield f"data: {json.dumps(end_event)}\n\n".encode('utf-8')
                    
                except Exception as e:
                    logger.error(f"Error in event stream: {str(e)}")
                    logger.error(traceback.format_exc())
                    error_event = {
                        'type': 'error',
                        'error': str(e),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    yield f"data: {json.dumps(error_event)}\n\n".encode('utf-8')
            
            response = StreamingHttpResponse(
                streaming_content=event_stream(),
                content_type='text/event-stream'
            )
            response['Cache-Control'] = 'no-cache'
            response['X-Accel-Buffering'] = 'no'
            return response
            
        except Chat.DoesNotExist:
            return JsonResponse({'error': 'Chat not found or access denied'}, status=404)
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=401)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=500)
        except BaseException as e:  # Catches ALL exceptions, including KeyboardInterrupt, SystemExit
            logger.critical(f"Critical error: {str(e)}")
            logger.critical(traceback.format_exc())
            return JsonResponse({'error (BaseException)': str(e)}, status=500)