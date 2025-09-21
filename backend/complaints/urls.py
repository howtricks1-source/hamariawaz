from django.urls import path, include
from . import views

app_name = 'complaints'

urlpatterns = [
    # Complaint endpoints
    path('', views.ComplaintListView.as_view(), name='complaint-list'),
    path('create/', views.ComplaintCreateView.as_view(), name='complaint-create'),
    path('<uuid:id>/', views.ComplaintDetailView.as_view(), name='complaint-detail'),
    path('forward/', views.forward_complaint, name='complaint-forward'),
    path('<uuid:complaint_id>/responses/', views.ComplaintResponseCreateView.as_view(), name='complaint-response-create'),
    path('<uuid:complaint_id>/comments/', views.ComplaintCommentListView.as_view(), name='complaint-comment-list'),
    path('<uuid:complaint_id>/comments/', views.ComplaintCommentCreateView.as_view(), name='complaint-comment-create'),
    path('comments/<int:comment_id>/reply/', views.reply_to_comment, name='comment-reply'),
    
    # Withdrawal endpoints
    path('withdrawals/', views.WithdrawalRequestListView.as_view(), name='withdrawal-list'),
    path('withdrawals/create/', views.WithdrawalRequestCreateView.as_view(), name='withdrawal-create'),
    path('withdrawals/<uuid:id>/', views.WithdrawalRequestDetailView.as_view(), name='withdrawal-detail'),
    
    # Utility endpoints
    path('categories/', views.ComplaintCategoryListView.as_view(), name='category-list'),
    path('departments/', views.DepartmentListView.as_view(), name='department-list'),
    path('files/<int:file_id>/download/', views.download_file, name='file-download'),
    path('statistics/', views.complaint_statistics, name='complaint-statistics'),
]

