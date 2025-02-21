# Generated by Django 5.1.5 on 2025-02-16 03:22

import django.core.serializers.json
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Chat',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_message_at', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('model', models.CharField(default='claude-3-5-sonnet', max_length=50)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'chats',
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('content', models.TextField()),
                ('role', models.CharField(max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='chat.chat')),
            ],
            options={
                'db_table': 'messages',
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='Sequence',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('gene_symbol', models.CharField(max_length=255)),
                ('anticodon', models.CharField(max_length=10)),
                ('isotype', models.CharField(max_length=10)),
                ('general_score', models.FloatField()),
                ('isotype_score', models.FloatField()),
                ('model_agreement', models.BooleanField()),
                ('features', models.JSONField(encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('locus', models.JSONField(encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('sequences', models.JSONField(encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('overview', models.JSONField(encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sequences', to='chat.chat')),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sequences', to='chat.message')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'sequences',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='chat',
            index=models.Index(fields=['user', '-last_message_at'], name='chats_user_id_6f7915_idx'),
        ),
        migrations.AddIndex(
            model_name='chat',
            index=models.Index(fields=['user', '-created_at'], name='chats_user_id_e04d4e_idx'),
        ),
        migrations.AddIndex(
            model_name='chat',
            index=models.Index(fields=['is_active'], name='chats_is_acti_9e50e9_idx'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['chat', '-created_at'], name='messages_chat_id_1405f3_idx'),
        ),
        migrations.AddIndex(
            model_name='sequence',
            index=models.Index(fields=['user', '-created_at'], name='sequences_user_id_a39c09_idx'),
        ),
        migrations.AddIndex(
            model_name='sequence',
            index=models.Index(fields=['chat', '-created_at'], name='sequences_chat_id_0bdee1_idx'),
        ),
        migrations.AddIndex(
            model_name='sequence',
            index=models.Index(fields=['message', '-created_at'], name='sequences_message_bb4856_idx'),
        ),
        migrations.AddIndex(
            model_name='sequence',
            index=models.Index(fields=['gene_symbol'], name='sequences_gene_sy_34c95f_idx'),
        ),
    ]
