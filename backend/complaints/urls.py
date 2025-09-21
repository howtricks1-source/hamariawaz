from django.urls import path
from . import views

app_name = 'complaints'

urlpatterns = [
    # Complaint CRUD
    path('', views.ComplaintListCreateView.as_view(), name='complaint_list_create'),
    path('<uuid:pk>/', views.ComplaintDetailView.as_view(), name='complaint_detail'),
    path('<uuid:pk>/comments/', views.ComplaintCommentListCreateView.as_view(), name='complaint_comments'),
    path('<uuid:pk>/files/', views.ComplaintFileListCreateView.as_view(), name='complaint_files'),
    path('<uuid:pk>/status/', views.ComplaintStatusUpdateView.as_view(), name='complaint_status_update'),
    path('<uuid:pk>/assign/', views.ComplaintAssignView.as_view(), name='complaint_assign'),
    path('<uuid:pk>/escalate/', views.ComplaintEscalateView.as_view(), name='complaint_escalate'),
    
    # Categories
    path('categories/', views.ComplaintCategoryListView.as_view(), name='category_list'),
    
    # File operations
    path('files/<int:pk>/', views.ComplaintFileDetailView.as_view(), name='file_detail'),
    path('files/<int:pk>/download/', views.download_complaint_file, name='file_download'),
    
    # Statistics
    path('stats/', views.ComplaintStatsView.as_view(), name='complaint_stats'),
    path('my-stats/', views.MyComplaintStatsView.as_view(), name='my_complaint_stats'),
]

