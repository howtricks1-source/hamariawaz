from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Avg, Count, Q
import uuid

User = get_user_model()


class AnalyticsReport(models.Model):
    """Generated analytics reports"""
    
    class ReportType(models.TextChoices):
        COMPLAINTS_SUMMARY = 'complaints_summary', _('Complaints Summary')
        DEPARTMENT_PERFORMANCE = 'department_performance', _('Department Performance')
        USER_ACTIVITY = 'user_activity', _('User Activity')
        RESOLUTION_TRENDS = 'resolution_trends', _('Resolution Trends')
        FEEDBACK_ANALYSIS = 'feedback_analysis', _('Feedback Analysis')
        CUSTOM = 'custom', _('Custom Report')
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        GENERATING = 'generating', _('Generating')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=50, choices=ReportType.choices)
    
    # Report parameters
    date_from = models.DateTimeField()
    date_to = models.DateTimeField()
    departments = models.ManyToManyField(
        'accounts.Department',
        blank=True,
        related_name='analytics_reports'
    )
    
    # Report data
    data = models.JSONField(default=dict)
    charts_config = models.JSONField(default=dict)
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    
    # Access control
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_reports')
    is_public = models.BooleanField(default=False)
    allowed_roles = models.JSONField(
        default=list,
        help_text="List of roles that can access this report"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'analytics_reports'
        verbose_name = _('Analytics Report')
        verbose_name_plural = _('Analytics Reports')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_report_type_display()}"
    
    def is_expired(self):
        """Check if report has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def can_access(self, user):
        """Check if user can access this report"""
        if self.created_by == user or user.is_admin_user:
            return True
        
        if self.is_public:
            return True
        
        if user.role in self.allowed_roles:
            return True
        
        return False


class DashboardWidget(models.Model):
    """Dashboard widgets configuration"""
    
    class WidgetType(models.TextChoices):
        CHART = 'chart', _('Chart')
        METRIC = 'metric', _('Metric')
        TABLE = 'table', _('Table')
        LIST = 'list', _('List')
        PROGRESS = 'progress', _('Progress Bar')
    
    class ChartType(models.TextChoices):
        LINE = 'line', _('Line Chart')
        BAR = 'bar', _('Bar Chart')
        PIE = 'pie', _('Pie Chart')
        DOUGHNUT = 'doughnut', _('Doughnut Chart')
        AREA = 'area', _('Area Chart')
        SCATTER = 'scatter', _('Scatter Plot')
    
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Widget configuration
    widget_type = models.CharField(max_length=20, choices=WidgetType.choices)
    chart_type = models.CharField(
        max_length=20,
        choices=ChartType.choices,
        blank=True,
        null=True
    )
    
    # Data source configuration
    data_source = models.CharField(max_length=100)  # Model or API endpoint
    query_params = models.JSONField(default=dict)
    refresh_interval = models.PositiveIntegerField(
        default=300,
        help_text="Refresh interval in seconds"
    )
    
    # Display configuration
    position_x = models.PositiveIntegerField(default=0)
    position_y = models.PositiveIntegerField(default=0)
    width = models.PositiveIntegerField(default=6)  # Grid columns (1-12)
    height = models.PositiveIntegerField(default=4)  # Grid rows
    
    # Styling
    color_scheme = models.JSONField(default=list)
    custom_css = models.TextField(blank=True)
    
    # Access control
    roles = models.JSONField(
        default=list,
        help_text="List of roles that can see this widget"
    )
    departments = models.ManyToManyField(
        'accounts.Department',
        blank=True,
        related_name='dashboard_widgets'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dashboard_widgets'
        verbose_name = _('Dashboard Widget')
        verbose_name_plural = _('Dashboard Widgets')
        ordering = ['position_y', 'position_x']
    
    def __str__(self):
        return f"{self.title} ({self.get_widget_type_display()})"


class UserDashboard(models.Model):
    """User-specific dashboard configurations"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dashboard')
    widgets = models.ManyToManyField(
        DashboardWidget,
        through='UserDashboardWidget',
        related_name='user_dashboards'
    )
    
    # Layout configuration
    layout_config = models.JSONField(default=dict)
    theme = models.CharField(
        max_length=20,
        choices=[
            ('light', 'Light'),
            ('dark', 'Dark'),
            ('auto', 'Auto'),
        ],
        default='light'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_dashboards'
        verbose_name = _('User Dashboard')
        verbose_name_plural = _('User Dashboards')
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Dashboard"


class UserDashboardWidget(models.Model):
    """Many-to-many relationship between users and dashboard widgets"""
    
    user_dashboard = models.ForeignKey(UserDashboard, on_delete=models.CASCADE)
    widget = models.ForeignKey(DashboardWidget, on_delete=models.CASCADE)
    
    # User-specific widget configuration
    position_x = models.PositiveIntegerField()
    position_y = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    
    # User customizations
    custom_title = models.CharField(max_length=200, blank=True)
    custom_config = models.JSONField(default=dict)
    is_visible = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_dashboard_widgets'
        unique_together = ['user_dashboard', 'widget']
        verbose_name = _('User Dashboard Widget')
        verbose_name_plural = _('User Dashboard Widgets')
    
    def __str__(self):
        return f"{self.user_dashboard.user.get_full_name()} - {self.widget.title}"


class SystemMetric(models.Model):
    """System-wide metrics tracking"""
    
    class MetricType(models.TextChoices):
        COUNTER = 'counter', _('Counter')
        GAUGE = 'gauge', _('Gauge')
        HISTOGRAM = 'histogram', _('Histogram')
        SUMMARY = 'summary', _('Summary')
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    metric_type = models.CharField(max_length=20, choices=MetricType.choices)
    
    # Current value
    current_value = models.FloatField(default=0)
    previous_value = models.FloatField(default=0)
    
    # Metadata
    unit = models.CharField(max_length=20, blank=True)
    tags = models.JSONField(default=dict)
    
    # Thresholds for alerts
    warning_threshold = models.FloatField(null=True, blank=True)
    critical_threshold = models.FloatField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'system_metrics'
        verbose_name = _('System Metric')
        verbose_name_plural = _('System Metrics')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name}: {self.current_value} {self.unit}"
    
    @property
    def change_percentage(self):
        """Calculate percentage change from previous value"""
        if self.previous_value == 0:
            return 0
        return ((self.current_value - self.previous_value) / self.previous_value) * 100
    
    def is_warning(self):
        """Check if metric is in warning state"""
        if self.warning_threshold is not None:
            return self.current_value >= self.warning_threshold
        return False
    
    def is_critical(self):
        """Check if metric is in critical state"""
        if self.critical_threshold is not None:
            return self.current_value >= self.critical_threshold
        return False


class MetricHistory(models.Model):
    """Historical data for system metrics"""
    
    metric = models.ForeignKey(
        SystemMetric,
        on_delete=models.CASCADE,
        related_name='history'
    )
    value = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Additional context
    context = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'metric_history'
        verbose_name = _('Metric History')
        verbose_name_plural = _('Metric Histories')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['metric', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.metric.name}: {self.value} at {self.timestamp}"


class PerformanceSnapshot(models.Model):
    """Daily/weekly/monthly performance snapshots"""
    
    class Period(models.TextChoices):
        DAILY = 'daily', _('Daily')
        WEEKLY = 'weekly', _('Weekly')
        MONTHLY = 'monthly', _('Monthly')
        QUARTERLY = 'quarterly', _('Quarterly')
        YEARLY = 'yearly', _('Yearly')
    
    period = models.CharField(max_length=20, choices=Period.choices)
    date = models.DateField()
    
    # Complaint metrics
    total_complaints = models.PositiveIntegerField(default=0)
    new_complaints = models.PositiveIntegerField(default=0)
    resolved_complaints = models.PositiveIntegerField(default=0)
    pending_complaints = models.PositiveIntegerField(default=0)
    avg_resolution_time = models.FloatField(default=0)  # in days
    
    # Feedback metrics
    total_feedback = models.PositiveIntegerField(default=0)
    new_feedback = models.PositiveIntegerField(default=0)
    avg_feedback_rating = models.FloatField(default=0)
    
    # User metrics
    active_users = models.PositiveIntegerField(default=0)
    new_registrations = models.PositiveIntegerField(default=0)
    
    # Department-specific data
    department_data = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'performance_snapshots'
        verbose_name = _('Performance Snapshot')
        verbose_name_plural = _('Performance Snapshots')
        unique_together = ['period', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.get_period_display()} snapshot for {self.date}"


# Signal to create default dashboard for new users
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_dashboard(sender, instance, created, **kwargs):
    if created:
        UserDashboard.objects.create(user=instance)

