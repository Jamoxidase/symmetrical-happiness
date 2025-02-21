from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import Chat, Message

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_link', 'title', 'message_count', 'created_at', 'updated_at', 'view_messages')
    list_filter = ('created_at', 'updated_at', 'user')
    search_fields = ('title', 'user__username', 'user__email', 'messages__content')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'message_count')
    
    def get_queryset(self, request):
        """Add message count to queryset."""
        queryset = super().get_queryset(request)
        return queryset.annotate(
            message_count=Count('messages')
        )
    
    def message_count(self, obj):
        """Display message count with link to messages."""
        count = obj.message_count
        url = reverse('admin:chat_message_changelist') + f'?chat__id={obj.id}'
        return format_html('<a href="{}">{} messages</a>', url, count)
    message_count.admin_order_field = 'message_count'
    message_count.short_description = 'Messages'
    
    def user_link(self, obj):
        """Display user with link to user admin."""
        url = reverse('admin:authentication_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_link.admin_order_field = 'user'
    user_link.short_description = 'User'
    
    def view_messages(self, obj):
        """Link to view messages in this chat."""
        url = reverse('admin:chat_message_changelist') + f'?chat__id={obj.id}'
        return format_html('<a class="button" href="{}">View Messages</a>', url)
    view_messages.short_description = 'Messages'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat_link', 'role', 'truncated_content', 'created_at')
    list_filter = ('role', 'created_at', 'chat__user')
    search_fields = ('content', 'chat__title', 'chat__user__username', 'chat__user__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'chat_link', 'user_link')
    
    def truncated_content(self, obj):
        """Display truncated message content."""
        max_length = 100
        content = obj.content
        if len(content) > max_length:
            return f"{content[:max_length]}..."
        return content
    truncated_content.short_description = 'Content'
    
    def chat_link(self, obj):
        """Display chat with link to chat admin."""
        url = reverse('admin:chat_chat_change', args=[obj.chat.id])
        return format_html('<a href="{}">{}</a>', url, obj.chat.title)
    chat_link.admin_order_field = 'chat'
    chat_link.short_description = 'Chat'
    
    def user_link(self, obj):
        """Display user with link to user admin."""
        url = reverse('admin:authentication_user_change', args=[obj.chat.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.chat.user.email)
    user_link.admin_order_field = 'chat__user'
    user_link.short_description = 'User'
    
    fieldsets = (
        (None, {
            'fields': ('chat_link', 'user_link', 'role', 'content')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
