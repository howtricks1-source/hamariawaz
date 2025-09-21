from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/widgets/', views.DashboardWidgetListView.as_view(), name='dashboard_widgets'),
    path('dashboard/widgets/<int:pk>/', views.DashboardWidgetDetailView.as_view(), name='widget_detail'),
    
    # Reports
    path('reports/', views.AnalyticsReportListCreateView.as_view(), name='report_list_create'),
    path('reports/<uuid:pk>/', views.AnalyticsReportDetailView.as_view(), name='report_detail'),
    path('reports/<uuid:pk>/download/', views.download_report, name='report_download'),
    
    # Charts and data
    path('charts/complaints-by-status/', views.complaints_by_status_chart, name='complaints_by_status'),
    path('charts/complaints-by-department/', views.complaints_by_department_chart, name='complaints_by_department'),
    path('charts/complaints-trend/', views.complaints_trend_chart, name='complaints_trend'),
    path('charts/resolution-time/', views.resolution_time_chart, name='resolution_time'),
    path('charts/feedback-ratings/', views.feedback_ratings_chart, name='feedback_ratings'),
    
    # System metrics
    path('metrics/', views.SystemMetricListView.as_view(), name='metrics'),
    path('metrics/<int:pk>/', views.SystemMetricDetailView.as_view(), name='metric_detail'),
    path('metrics/<int:pk>/history/', views.MetricHistoryView.as_view(), name='metric_history'),
    
    # Performance snapshots
    path('snapshots/', views.PerformanceSnapshotListView.as_view(), name='snapshots'),
    path('snapshots/<int:pk>/', views.PerformanceSnapshotDetailView.as_view(), name='snapshot_detail'),
    
    # Export functionality
    path('export/complaints/', views.export_complaints, name='export_complaints'),
    path('export/feedback/', views.export_feedback, name='export_feedback'),
    path('export/users/', views.export_users, name='export_users'),
]

