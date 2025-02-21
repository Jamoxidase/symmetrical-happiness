from django.urls import path
from .views import ChatView, ChatHistoryView, ChatMessageView, ChatManagementView

urlpatterns = [
    # List all chats and create new chat
    path("", ChatView.as_view(), name="chat-list-create"),

    # Get chat history
    path("<uuid:chat_id>/", ChatHistoryView.as_view(), name="chat-history"),

    # Send message to existing chat
    path("<uuid:chat_id>/message/", ChatMessageView.as_view(), name="chat-message"),

    # Update or delete chat
    path("<uuid:chat_id>/manage/", ChatManagementView.as_view(), name="chat-manage"),
]
