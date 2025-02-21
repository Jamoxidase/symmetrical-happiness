import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
import json


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        # Set available models for new user
        user.set_available_models(settings.AVAILABLE_MODELS)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class UserRole(models.TextChoices):
    BASIC = 'basic', _('Basic')
    PREMIUM = 'premium', _('Premium')
    ADMIN = 'admin', _('Admin')

class User(AbstractUser):
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(max_length=150, null=True, blank=True)
    
    # Security and access control
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.BASIC
    )
    is_active = models.BooleanField(default=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True)
    
    # Rate limiting and quotas
    daily_request_count = models.IntegerField(default=0)
    last_request_reset = models.DateTimeField(default=timezone.now)  # Changed from auto_now_add
    max_daily_requests = models.IntegerField(default=1000)  # Configurable per role
    
    # Token management
    refresh_token_jti = models.CharField(max_length=64, null=True, blank=True)  # JWT ID for the current refresh token
    
    # Model access
    available_models = models.TextField(
        default='[]',
        help_text="JSON list of LLM models this user has access to"
    )

    def get_available_models(self):
        """Get the list of available models."""
        try:
            return json.loads(self.available_models)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_available_models(self, models_list):
        """Set the list of available models."""
        self.available_models = json.dumps(models_list)
        self.save()
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'auth_user'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_rate_limits(self) -> dict:
        """Get rate limits based on user role."""
        limits = {
            UserRole.BASIC: {
                'daily_requests': 1000,
                'concurrent_chats': 3,
                'max_tokens': 2000
            },
            UserRole.PREMIUM: {
                'daily_requests': 5000,
                'concurrent_chats': 10,
                'max_tokens': 4000
            },
            UserRole.ADMIN: {
                'daily_requests': 10000,
                'concurrent_chats': 20,
                'max_tokens': 8000
            }
        }
        return limits.get(self.role, limits[UserRole.BASIC])
    
    def check_rate_limit(self) -> bool:
        """Check if user has exceeded their rate limit."""
        limits = self.get_rate_limits()
        
        # Reset daily counter if needed
        now = timezone.now()
        if (now - self.last_request_reset).days > 0:
            self.daily_request_count = 0
            self.last_request_reset = now
            self.save()
        
        return self.daily_request_count < limits['daily_requests']
    
    def increment_request_count(self):
        """Increment the daily request counter."""
        self.daily_request_count += 1
        self.save()
