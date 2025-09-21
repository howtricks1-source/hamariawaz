from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Custom User model with role-based access"""
    
    class Role(models.TextChoices):
        STUDENT = 'student', _('Student')
        STAFF = 'staff', _('Staff')
        HEAD = 'head', _('Department Head')
        VC = 'vc', _('Vice Chancellor')
        ADMIN = 'admin', _('Admin')
    
    # Basic Information
    email = models.EmailField(_('email address'), unique=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    
    # Role and Department
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text=_('User role in the system')
    )
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    
    # Student specific fields
    student_id = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text=_('Student registration number')
    )
    semester = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('Current semester (for students)')
    )
    
    # Staff specific fields
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text=_('Employee ID (for staff/faculty)')
    )
    designation = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Job designation (for staff/faculty)')
    )
    
    # Profile Information
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True
    )
    bio = models.TextField(max_length=500, blank=True)
    
    # Status and Timestamps
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Email as username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name
    
    @property
    def is_student(self):
        return self.role == self.Role.STUDENT
    
    @property
    def is_staff_member(self):
        return self.role == self.Role.STAFF
    
    @property
    def is_department_head(self):
        return self.role == self.Role.HEAD
    
    @property
    def is_vc(self):
        return self.role == self.Role.VC
    
    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN
    
    def can_view_complaint(self, complaint):
        """Check if user can view a specific complaint"""
        if self.is_admin_user or self.is_vc:
            return True
        
        if self.is_student:
            return complaint.student == self
        
        if self.is_department_head:
            return complaint.department == self.department
        
        if self.is_staff_member:
            return complaint.assigned_to == self or complaint.department == self.department
        
        return False
    
    def can_edit_complaint(self, complaint):
        """Check if user can edit a specific complaint"""
        if self.is_admin_user:
            return True
        
        if self.is_student:
            return complaint.student == self and complaint.status in ['pending', 'in_progress']
        
        if self.is_vc or self.is_department_head or self.is_staff_member:
            return self.can_view_complaint(complaint)
        
        return False


class Department(models.Model):
    """University departments"""
    
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    head = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_department',
        limit_choices_to={'role': User.Role.HEAD}
    )
    
    # Contact Information
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=17, blank=True)
    office_location = models.CharField(max_length=200, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'departments'
        verbose_name = _('Department')
        verbose_name_plural = _('Departments')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def total_complaints(self):
        """Get total complaints for this department"""
        return self.complaints.count()
    
    @property
    def pending_complaints(self):
        """Get pending complaints for this department"""
        return self.complaints.filter(status='pending').count()
    
    @property
    def resolved_complaints(self):
        """Get resolved complaints for this department"""
        return self.complaints.filter(status='resolved').count()


class UserProfile(models.Model):
    """Extended user profile information"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Notification Preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)
    
    # Privacy Settings
    profile_visibility = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('department', 'Department Only'),
            ('private', 'Private'),
        ],
        default='department'
    )
    
    # Additional Information
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=17, blank=True)
    
    # Academic Information (for students)
    admission_year = models.PositiveIntegerField(null=True, blank=True)
    graduation_year = models.PositiveIntegerField(null=True, blank=True)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    
    # Professional Information (for staff)
    join_date = models.DateField(null=True, blank=True)
    qualification = models.CharField(max_length=200, blank=True)
    experience_years = models.PositiveIntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Profile"


# Signal to create user profile
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)

