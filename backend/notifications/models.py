from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid

User = get_user_model()


class NotificationType(models.Model):
    """Types of notifications"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default="#007bff")
    
    # Email template settings
    email_template = models.CharField(max_length=200, blank=True)
    email_subject_template = models.CharField(max_length=200, blank=True)
    
    # Default settings
    default_email_enabled = models.BooleanField(default=True)
    default_push_enabled = models.BooleanField(default=True)
    default_sms_enabled = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notification_types'
        verbose_name = _('Notification Type')
        verbose_name_plural = _('Notification Types')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Notification(models.Model):
    """Individual notifications"""
    
    class Priority(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        URGENT = 'urgent', _('Urgent')
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.ForeignKey(
        NotificationType,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    # Content
    title = models.CharField(max_length=200)
    message = models.TextField()
    action_url = models.URLField(blank=True, help_text="URL to redirect when clicked")
    
    # Generic relation to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Status
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    
    # Delivery channels
    email_sent = models.BooleanField(default=False)
    push_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'notifications'
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['recipient', 'created_at']),
            models.Index(fields=['notification_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.recipient.get_full_name()}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def get_priority_color(self):
        """Get color for priority display"""
        colors = {
            self.Priority.LOW: '#28a745',
            self.Priority.MEDIUM: '#ffc107',
            self.Priority.HIGH: '#fd7e14',
            self.Priority.URGENT: '#dc3545',
        }
        return colors.get(self.priority, '#6c757d')


class NotificationPreference(models.Model):
    """User notification preferences"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    notification_type = models.ForeignKey(
        NotificationType,
        on_delete=models.CASCADE
    )
    
    # Channel preferences
    email_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    
    # Timing preferences
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_preferences'
        verbose_name = _('Notification Preference')
        verbose_name_plural = _('Notification Preferences')
        unique_together = ['user', 'notification_type']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.notification_type.name}"


class EmailTemplate(models.Model):
    """Email templates for notifications"""
    
    name = models.CharField(max_length=100, unique=True)
    subject = models.CharField(max_length=200)
    html_content = models.TextField()
    text_content = models.TextField(blank=True)
    
    # Template variables documentation
    variables = models.JSONField(
        default=dict,
        help_text="Available template variables and their descriptions"
    )
    
    # Settings
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'email_templates'
        verbose_name = _('Email Template')
        verbose_name_plural = _('Email Templates')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class NotificationBatch(models.Model):
    """Batch notifications for bulk sending"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PROCESSING = 'processing', _('Processing')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Recipients
    recipients = models.ManyToManyField(User, related_name='notification_batches')
    
    # Content
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Statistics
    total_recipients = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Created by
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_notification_batches'
    )
    
    class Meta:
        db_table = 'notification_batches'
        verbose_name = _('Notification Batch')
        verbose_name_plural = _('Notification Batches')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.total_recipients} recipients)"


class NotificationLog(models.Model):
    """Log of notification delivery attempts"""
    
    class Status(models.TextChoices):
        SUCCESS = 'success', _('Success')
        FAILED = 'failed', _('Failed')
        PENDING = 'pending', _('Pending')
        RETRY = 'retry', _('Retry')
    
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='delivery_logs'
    )
    channel = models.CharField(
        max_length=20,
        choices=[
            ('email', 'Email'),
            ('push', 'Push Notification'),
            ('sms', 'SMS'),
        ]
    )
    status = models.CharField(max_length=20, choices=Status.choices)
    
    # Delivery details
    provider = models.CharField(max_length=100, blank=True)
    provider_message_id = models.CharField(max_length=200, blank=True)
    error_message = models.TextField(blank=True)
    
    # Retry information
    retry_count = models.PositiveIntegerField(default=0)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notification_logs'
        verbose_name = _('Notification Log')
        verbose_name_plural = _('Notification Logs')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification.title} - {self.channel} - {self.status}"


# Signal to create default notification preferences
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    if created:
        # Create default notification preferences for all notification types
        for notification_type in NotificationType.objects.filter(is_active=True):
            NotificationPreference.objects.get_or_create(
                user=instance,
                notification_type=notification_type,
                defaults={
                    'email_enabled': notification_type.default_email_enabled,
                    'push_enabled': notification_type.default_push_enabled,
                    'sms_enabled': notification_type.default_sms_enabled,
                }
            )

