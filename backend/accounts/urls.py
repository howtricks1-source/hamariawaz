from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication - matching your exact endpoints
    path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    
    # User management (admin only)
    path('users/', views.UserListCreateView.as_view(), name='user_list_create'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/bulk-action/', views.bulk_user_action, name='bulk_user_action'),
    path('users/search/', views.UserSearchView.as_view(), name='user_search'),
    path('users/stats/', views.UserStatsView.as_view(), name='user_stats'),
    
    # Additional profile endpoints
    path('profile/password/', views.PasswordChangeView.as_view(), name='password_change'),
    path('current-user/', views.current_user, name='current_user'),
    
    # Departments
    path('departments/', views.DepartmentListView.as_view(), name='department_list'),
    path('departments/<int:pk>/', views.DepartmentDetailView.as_view(), name='department_detail'),
    
    # Utility endpoints
    path('check-email/', views.check_email_availability, name='check_email'),
    path('check-student-id/', views.check_student_id_availability, name='check_student_id'),
]
