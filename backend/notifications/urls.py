from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # User notifications
    path('', views.NotificationListView.as_view(), name='notification_list'),
    path('<uuid:pk>/', views.NotificationDetailView.as_view(), name='notification_detail'),
    path('<uuid:pk>/read/', views.mark_notification_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_notifications_read, name='mark_all_read'),
    path('unread-count/', views.unread_notification_count, name='unread_count'),
    
    # Notification preferences
    path('preferences/', views.NotificationPreferenceListView.as_view(), name='preferences'),
    path('preferences/<int:pk>/', views.NotificationPreferenceUpdateView.as_view(), name='preference_update'),
    
    # Bulk notifications (admin/authority only)
    path('bulk/', views.BulkNotificationCreateView.as_view(), name='bulk_create'),
    path('batches/', views.NotificationBatchListView.as_view(), name='batch_list'),
    path('batches/<uuid:pk>/', views.NotificationBatchDetailView.as_view(), name='batch_detail'),
    
    # Templates (admin only)
    path('templates/', views.EmailTemplateListView.as_view(), name='template_list'),
    path('templates/<int:pk>/', views.EmailTemplateDetailView.as_view(), name='template_detail'),
]

