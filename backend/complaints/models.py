from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.utils import timezone
import uuid
import os

User = get_user_model()


def complaint_file_upload_path(instance, filename):
    """Generate upload path for complaint files"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('complaints', str(instance.complaint.id), filename)


class ComplaintCategory(models.Model):
    """Categories for complaints"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class name")
    color = models.CharField(max_length=7, default="#007bff", help_text="Hex color code")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'complaint_categories'
        verbose_name = _('Complaint Category')
        verbose_name_plural = _('Complaint Categories')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Complaint(models.Model):
    """Main complaint model"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        IN_PROGRESS = 'in_progress', _('In Progress')
        RESOLVED = 'resolved', _('Resolved')
        REJECTED = 'rejected', _('Rejected')
        ESCALATED = 'escalated', _('Escalated')
    
    class Priority(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        URGENT = 'urgent', _('Urgent')
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(
        ComplaintCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='complaints'
    )
    
    # Relationships
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submitted_complaints',
        limit_choices_to={'role': User.Role.STUDENT}
    )
    department = models.ForeignKey(
        'accounts.Department',
        on_delete=models.SET_NULL,
        null=True,
        related_name='complaints'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_complaints',
        limit_choices_to={'role__in': [User.Role.STAFF, User.Role.HEAD, User.Role.VC]}
    )
    
    # Status and Priority
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    
    # Tracking Information
    complaint_number = models.CharField(max_length=20, unique=True, editable=False)
    is_anonymous = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    
    # Additional Information
    location = models.CharField(max_length=200, blank=True)
    incident_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'complaints'
        verbose_name = _('Complaint')
        verbose_name_plural = _('Complaints')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['department', 'status']),
            models.Index(fields=['assigned_to', 'status']),
        ]
    
    def __str__(self):
        return f"{self.complaint_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.complaint_number:
            # Generate complaint number
            year = timezone.now().year
            count = Complaint.objects.filter(created_at__year=year).count() + 1
            self.complaint_number = f"CMP{year}{count:05d}"
        
        # Set resolved_at when status changes to resolved
        if self.status == self.Status.RESOLVED and not self.resolved_at:
            self.resolved_at = timezone.now()
        elif self.status != self.Status.RESOLVED:
            self.resolved_at = None
        
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Check if complaint is overdue"""
        if self.due_date and self.status not in [self.Status.RESOLVED, self.Status.REJECTED]:
            return timezone.now() > self.due_date
        return False
    
    @property
    def days_since_created(self):
        """Get days since complaint was created"""
        return (timezone.now() - self.created_at).days
    
    @property
    def resolution_time(self):
        """Get resolution time in days"""
        if self.resolved_at:
            return (self.resolved_at - self.created_at).days
        return None
    
    def get_status_display_color(self):
        """Get color for status display"""
        colors = {
            self.Status.PENDING: '#ffc107',
            self.Status.IN_PROGRESS: '#007bff',
            self.Status.RESOLVED: '#28a745',
            self.Status.REJECTED: '#dc3545',
            self.Status.ESCALATED: '#fd7e14',
        }
        return colors.get(self.status, '#6c757d')
    
    def get_priority_display_color(self):
        """Get color for priority display"""
        colors = {
            self.Priority.LOW: '#28a745',
            self.Priority.MEDIUM: '#ffc107',
            self.Priority.HIGH: '#fd7e14',
            self.Priority.URGENT: '#dc3545',
        }
        return colors.get(self.priority, '#6c757d')


class ComplaintFile(models.Model):
    """File attachments for complaints"""
    
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name='files'
    )
    file = models.FileField(
        upload_to=complaint_file_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif']
            )
        ]
    )
    original_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    content_type = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'complaint_files'
        verbose_name = _('Complaint File')
        verbose_name_plural = _('Complaint Files')
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.original_name} - {self.complaint.complaint_number}"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            self.original_name = self.file.name
        super().save(*args, **kwargs)
    
    @property
    def file_size_mb(self):
        """Get file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)


class ComplaintComment(models.Model):
    """Comments on complaints"""
    
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    is_internal = models.BooleanField(
        default=False,
        help_text="Internal comments are only visible to staff"
    )
    is_status_update = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'complaint_comments'
        verbose_name = _('Complaint Comment')
        verbose_name_plural = _('Complaint Comments')
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author.get_full_name()} on {self.complaint.complaint_number}"


class ComplaintStatusHistory(models.Model):
    """Track status changes for complaints"""
    
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    old_status = models.CharField(max_length=20, choices=Complaint.Status.choices)
    new_status = models.CharField(max_length=20, choices=Complaint.Status.choices)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'complaint_status_history'
        verbose_name = _('Complaint Status History')
        verbose_name_plural = _('Complaint Status Histories')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.complaint.complaint_number}: {self.old_status} → {self.new_status}"


class ComplaintAssignmentHistory(models.Model):
    """Track assignment changes for complaints"""
    
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name='assignment_history'
    )
    old_assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='old_assignments'
    )
    new_assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='new_assignments'
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assignment_actions'
    )
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'complaint_assignment_history'
        verbose_name = _('Complaint Assignment History')
        verbose_name_plural = _('Complaint Assignment Histories')
        ordering = ['-created_at']
    
    def __str__(self):
        old_name = self.old_assignee.get_full_name() if self.old_assignee else "Unassigned"
        new_name = self.new_assignee.get_full_name() if self.new_assignee else "Unassigned"
        return f"{self.complaint.complaint_number}: {old_name} → {new_name}"

