import uuid
from django.db import models
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder



class Chat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    model = models.CharField(max_length=50, default=settings.DEFAULT_LLM_MODEL)

    class Meta:
        db_table = 'chats'
        indexes = [
            models.Index(fields=['user', '-last_message_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_active']),
        ]
    
    def get_preview(self) -> str:
        """Get a preview of the last message in the chat."""
        try:
            last_message = Message.objects.filter(chat=self).order_by('-created_at').first()
            if last_message:
                return last_message.content
        except Exception:
            return ""


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    role = models.CharField(max_length=50)  # 'user' or 'assistant'
    created_at = models.DateTimeField(auto_now_add=True)
    model = models.CharField(max_length=50, null=True)  # Store which model was requested/used
    
    class Meta:
        db_table = 'messages'
        indexes = [
            models.Index(fields=['chat', '-created_at']),
        ]
        ordering = ['created_at']


class Sequence(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='sequences')
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='sequences')
    
    # tRNA specific fields
    gene_symbol = models.CharField(max_length=255)
    anticodon = models.CharField(max_length=10)
    isotype = models.CharField(max_length=10)
    general_score = models.FloatField()
    isotype_score = models.FloatField()
    model_agreement = models.BooleanField()
    features = models.JSONField(encoder=DjangoJSONEncoder)
    locus = models.JSONField(encoder=DjangoJSONEncoder)
    sequences = models.JSONField(encoder=DjangoJSONEncoder)  # Contains different sequence types
    overview = models.JSONField(encoder=DjangoJSONEncoder)  # Contains modifications and other data
    images = models.JSONField(encoder=DjangoJSONEncoder, default=dict)  # Contains cloverleaf and other structural images
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sequences'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['chat', '-created_at']),
            models.Index(fields=['message', '-created_at']),
            models.Index(fields=['gene_symbol']),
        ]
        ordering = ['-created_at']

    def to_dict(self):
        """Convert sequence to dictionary format for SSE."""
        return {
            'type': 'sequence_data',
            'data': {
                'id': str(self.id),
                'gene_symbol': self.gene_symbol,
                'anticodon': self.anticodon,
                'isotype': self.isotype,
                'general_score': self.general_score,
                'isotype_score': self.isotype_score,
                'model_agreement': self.model_agreement,
                'features': self.features,
                'locus': self.locus,
                'sequences': self.sequences,
                'overview': self.overview,
                'images': self.images,
                'created_at': self.created_at.isoformat(),
            }
        }
