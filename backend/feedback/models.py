from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid

User = get_user_model()


class FeedbackCategory(models.Model):
    """Categories for feedback"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default="#28a745")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feedback_categories'
        verbose_name = _('Feedback Category')
        verbose_name_plural = _('Feedback Categories')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Feedback(models.Model):
    """Student feedback model"""
    
    class Type(models.TextChoices):
        SUGGESTION = 'suggestion', _('Suggestion')
        COMPLIMENT = 'compliment', _('Compliment')
        CONCERN = 'concern', _('Concern')
        GENERAL = 'general', _('General Feedback')
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        REVIEWED = 'reviewed', _('Reviewed')
        ACKNOWLEDGED = 'acknowledged', _('Acknowledged')
        IMPLEMENTED = 'implemented', _('Implemented')
        REJECTED = 'rejected', _('Rejected')
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    content = models.TextField()
    feedback_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.GENERAL
    )
    category = models.ForeignKey(
        FeedbackCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='feedbacks'
    )
    
    # Relationships
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submitted_feedbacks',
        limit_choices_to={'role': User.Role.STUDENT}
    )
    department = models.ForeignKey(
        'accounts.Department',
        on_delete=models.SET_NULL,
        null=True,
        related_name='feedbacks'
    )
    
    # Status and Processing
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_feedbacks'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Settings
    is_anonymous = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    allow_contact = models.BooleanField(
        default=True,
        help_text="Allow authorities to contact for clarification"
    )
    
    # Rating (optional)
    rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Rating from 1-5 stars"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'feedbacks'
        verbose_name = _('Feedback')
        verbose_name_plural = _('Feedbacks')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['department', 'status']),
            models.Index(fields=['feedback_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.student.get_full_name()}"
    
    def save(self, *args, **kwargs):
        # Set reviewed_at when status changes to reviewed
        if self.status in [self.Status.REVIEWED, self.Status.ACKNOWLEDGED] and not self.reviewed_at:
            self.reviewed_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def days_since_created(self):
        """Get days since feedback was created"""
        return (timezone.now() - self.created_at).days
    
    def get_status_display_color(self):
        """Get color for status display"""
        colors = {
            self.Status.PENDING: '#ffc107',
            self.Status.REVIEWED: '#007bff',
            self.Status.ACKNOWLEDGED: '#17a2b8',
            self.Status.IMPLEMENTED: '#28a745',
            self.Status.REJECTED: '#dc3545',
        }
        return colors.get(self.status, '#6c757d')


class FeedbackResponse(models.Model):
    """Responses to feedback from authorities"""
    
    feedback = models.ForeignKey(
        Feedback,
        on_delete=models.CASCADE,
        related_name='responses'
    )
    responder = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='feedback_responses'
    )
    content = models.TextField()
    is_public = models.BooleanField(
        default=False,
        help_text="Make response visible to other students"
    )
    
    # Action taken
    action_taken = models.TextField(
        blank=True,
        help_text="Describe any action taken based on this feedback"
    )
    implementation_date = models.DateField(
        null=True,
        blank=True,
        help_text="When the suggested change was implemented"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'feedback_responses'
        verbose_name = _('Feedback Response')
        verbose_name_plural = _('Feedback Responses')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Response to {self.feedback.title} by {self.responder.get_full_name()}"


class FeedbackVote(models.Model):
    """Voting system for public feedback"""
    
    class VoteType(models.TextChoices):
        UPVOTE = 'upvote', _('Upvote')
        DOWNVOTE = 'downvote', _('Downvote')
    
    feedback = models.ForeignKey(
        Feedback,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vote_type = models.CharField(max_length=10, choices=VoteType.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feedback_votes'
        verbose_name = _('Feedback Vote')
        verbose_name_plural = _('Feedback Votes')
        unique_together = ['feedback', 'user']
    
    def __str__(self):
        return f"{self.user.get_full_name()} {self.vote_type}d {self.feedback.title}"


class FeedbackTag(models.Model):
    """Tags for categorizing feedback"""
    
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default="#007bff")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feedback_tags'
        verbose_name = _('Feedback Tag')
        verbose_name_plural = _('Feedback Tags')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class FeedbackTagAssignment(models.Model):
    """Many-to-many relationship between feedback and tags"""
    
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE)
    tag = models.ForeignKey(FeedbackTag, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feedback_tag_assignments'
        unique_together = ['feedback', 'tag']
        verbose_name = _('Feedback Tag Assignment')
        verbose_name_plural = _('Feedback Tag Assignments')
    
    def __str__(self):
        return f"{self.feedback.title} - {self.tag.name}"


# Add tags to feedback model
Feedback.add_to_class(
    'tags',
    models.ManyToManyField(
        FeedbackTag,
        through=FeedbackTagAssignment,
        related_name='feedbacks',
        blank=True
    )
)

