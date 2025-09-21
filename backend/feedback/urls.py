from django.urls import path
from . import views

app_name = 'feedback'

urlpatterns = [
    # Feedback endpoints - matching your exact structure
    path('', views.FeedbackListCreateView.as_view(), name='feedback_create'),  # POST /api/complaints/feedback/
    path('list/', views.FeedbackListCreateView.as_view(), name='feedback_list'),  # GET /api/complaints/feedback/list/
    path('<uuid:pk>/', views.FeedbackDetailView.as_view(), name='feedback_detail'),
    path('<uuid:pk>/respond/', views.FeedbackResponseCreateView.as_view(), name='feedback_respond'),
    path('<uuid:pk>/vote/', views.FeedbackVoteView.as_view(), name='feedback_vote'),
    
    # Categories and tags
    path('categories/', views.FeedbackCategoryListView.as_view(), name='category_list'),
    path('tags/', views.FeedbackTagListView.as_view(), name='tag_list'),
    
    # Public feedback
    path('public/', views.PublicFeedbackListView.as_view(), name='public_feedback'),
    
    # Statistics
    path('stats/', views.FeedbackStatsView.as_view(), name='feedback_stats'),
    path('my-stats/', views.MyFeedbackStatsView.as_view(), name='my_feedback_stats'),
]
