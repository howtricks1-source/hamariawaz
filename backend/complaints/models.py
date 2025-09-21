from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
import uuid
import os

User = get_user_model()

# Import Department from accounts app
from accounts.models import Department

class ComplaintCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#3182ce')  # Hex color
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Complaint Categories"
        ordering = ['name']

def complaint_file_path(instance, filename):
    """Generate file path for complaint attachments"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('complaints', str(instance.complaint.id), filename)

class Complaint(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
        ('escalated', 'Escalated'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    complaint_number = models.CharField(max_length=20, unique=True, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Relationships
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    category = models.ForeignKey(ComplaintCategory, on_delete=models.SET_NULL, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_complaints')
    
    # Flags
    is_anonymous = models.BooleanField(default=False)
    is_urgent = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.complaint_number:
            # Generate complaint number
            count = Complaint.objects.count() + 1
            self.complaint_number = f"CMP{count:06d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.complaint_number} - {self.title}"

    class Meta:
        ordering = ['-created_at']

class ComplaintFile(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(
        upload_to=complaint_file_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'txt'])]
    )
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    file_type = models.CharField(max_length=50)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.file:
            self.file_name = self.file.name
            self.file_size = self.file.size
            self.file_type = self.file.content_type or 'application/octet-stream'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.complaint.complaint_number} - {self.file_name}"

class ComplaintComment(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    is_internal = models.BooleanField(default=False)  # Internal comments not visible to students
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment on {self.complaint.complaint_number} by {self.author.get_full_name()}"

    class Meta:
        ordering = ['created_at']

class ComplaintResponse(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='responses')
    responder = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    is_final_response = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response to {self.complaint.complaint_number} by {self.responder.get_full_name()}"

    class Meta:
        ordering = ['created_at']

class ComplaintForward(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='forwards')
    forwarded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forwarded_complaints')
    forwarded_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_complaints')
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.complaint.complaint_number} forwarded to {self.forwarded_to.get_full_name()}"

    class Meta:
        ordering = ['-created_at']

class WithdrawalRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    complaint = models.OneToOneField(Complaint, on_delete=models.CASCADE, related_name='withdrawal_request')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdrawal_requests')
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_withdrawals')
    review_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Withdrawal request for {self.complaint.complaint_number}"

    class Meta:
        ordering = ['-created_at']

def withdrawal_file_path(instance, filename):
    """Generate file path for withdrawal supporting documents"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('withdrawals', str(instance.withdrawal_request.id), filename)

class WithdrawalFile(models.Model):
    withdrawal_request = models.ForeignKey(WithdrawalRequest, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(
        upload_to=withdrawal_file_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'txt'])]
    )
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    file_type = models.CharField(max_length=50)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.file:
            self.file_name = self.file.name
            self.file_size = self.file.size
            self.file_type = self.file.content_type or 'application/octet-stream'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Withdrawal file - {self.file_name}"

class ComplaintStatusHistory(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.complaint.complaint_number}: {self.old_status} → {self.new_status}"

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Complaint Status Histories"
