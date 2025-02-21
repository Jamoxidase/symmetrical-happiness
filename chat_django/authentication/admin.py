from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'chat_count', 'message_count', 'last_login', 'is_active', 'is_staff', 'view_chats')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'groups', 'last_login', 'date_joined')
    search_fields = ('email', 'chat__title', 'chat__messages__content')
    ordering = ('-last_login',)
    
    def get_queryset(self, request):
        """Add chat and message counts to queryset."""
        queryset = super().get_queryset(request)
        return queryset.annotate(
            chat_count=Count('chat', distinct=True),
            message_count=Count('chat__messages', distinct=True)
        )
    
    def chat_count(self, obj):
        """Display chat count with link to chats."""
        count = obj.chat_count
        url = reverse('admin:chat_chat_changelist') + f'?user__id={obj.id}'
        return format_html('<a href="{}">{} chats</a>', url, count)
    chat_count.admin_order_field = 'chat_count'
    chat_count.short_description = 'Chats'
    
    def message_count(self, obj):
        """Display message count with link to messages."""
        count = obj.message_count
        url = reverse('admin:chat_message_changelist') + f'?chat__user__id={obj.id}'
        return format_html('<a href="{}">{} messages</a>', url, count)
    message_count.admin_order_field = 'message_count'
    message_count.short_description = 'Messages'
    
    def view_chats(self, obj):
        """Link to view user's chats."""
        url = reverse('admin:chat_chat_changelist') + f'?user__id={obj.id}'
        return format_html('<a class="button" href="{}">View Chats</a>', url)
    view_chats.short_description = 'Chats'
    
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('Personal info'), {
            'fields': ('username',)
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields read-only when editing."""
        if obj:  # Editing an existing object
            return self.readonly_fields + ('last_login', 'date_joined')
        return self.readonly_fields
