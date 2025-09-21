from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import User, Department, UserProfile
from .serializers import (
    UserSerializer, UserRegistrationSerializer, UserCreateSerializer,
    UserUpdateSerializer, PasswordChangeSerializer, CustomTokenObtainPairSerializer,
    ProfileUpdateSerializer, UserListSerializer, DepartmentSerializer
)
from .permissions import (
    IsOwnerOrReadOnly, CanManageUsers, IsAdminUser, IsAuthorityUser
)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token obtain view"""
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Update last login IP
            user = authenticate(
                username=request.data.get('email'),
                password=request.data.get('password')
            )
            if user:
                user.last_login_ip = self.get_client_ip(request)
                user.save(update_fields=['last_login_ip'])
        
        return response
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserRegistrationView(generics.CreateAPIView):
    """User registration view (for students only)"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens for the new user
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Registration successful',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile view"""
    serializer_class = ProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class PasswordChangeView(APIView):
    """Password change view"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListCreateView(generics.ListCreateAPIView):
    """User list and create view (admin only)"""
    queryset = User.objects.all()
    permission_classes = [CanManageUsers]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'department', 'is_active', 'is_verified']
    search_fields = ['first_name', 'last_name', 'email', 'username', 'student_id', 'employee_id']
    ordering_fields = ['created_at', 'last_login', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserListSerializer
    
    def get_queryset(self):
        queryset = User.objects.select_related('department').all()
        
        # Filter by department if user is not admin/VC
        user = self.request.user
        if not (user.is_admin_user or user.is_vc):
            if user.department:
                queryset = queryset.filter(department=user.department)
            else:
                queryset = queryset.none()
        
        return queryset


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """User detail view (admin only)"""
    queryset = User.objects.all()
    permission_classes = [CanManageUsers]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_queryset(self):
        queryset = User.objects.select_related('department', 'profile').all()
        
        # Filter by department if user is not admin/VC
        user = self.request.user
        if not (user.is_admin_user or user.is_vc):
            if user.department:
                queryset = queryset.filter(department=user.department)
            else:
                queryset = queryset.none()
        
        return queryset


class DepartmentListView(generics.ListAPIView):
    """Department list view"""
    queryset = Department.objects.filter(is_active=True)
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class DepartmentDetailView(generics.RetrieveAPIView):
    """Department detail view"""
    queryset = Department.objects.filter(is_active=True)
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserStatsView(APIView):
    """User statistics view"""
    permission_classes = [IsAuthorityUser]
    
    def get(self, request):
        user = request.user
        
        # Base queryset
        if user.is_admin_user or user.is_vc:
            users_queryset = User.objects.all()
        elif user.department:
            users_queryset = User.objects.filter(department=user.department)
        else:
            users_queryset = User.objects.none()
        
        # Calculate statistics
        stats = {
            'total_users': users_queryset.count(),
            'active_users': users_queryset.filter(is_active=True).count(),
            'verified_users': users_queryset.filter(is_verified=True).count(),
            'students': users_queryset.filter(role=User.Role.STUDENT).count(),
            'staff': users_queryset.filter(role=User.Role.STAFF).count(),
            'heads': users_queryset.filter(role=User.Role.HEAD).count(),
            'vcs': users_queryset.filter(role=User.Role.VC).count(),
            'admins': users_queryset.filter(role=User.Role.ADMIN).count(),
        }
        
        # Recent registrations (last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        stats['recent_registrations'] = users_queryset.filter(
            created_at__gte=thirty_days_ago
        ).count()
        
        # Department-wise breakdown
        if user.is_admin_user or user.is_vc:
            department_stats = []
            for dept in Department.objects.filter(is_active=True):
                dept_users = users_queryset.filter(department=dept)
                department_stats.append({
                    'department': dept.name,
                    'total_users': dept_users.count(),
                    'students': dept_users.filter(role=User.Role.STUDENT).count(),
                    'staff': dept_users.filter(role=User.Role.STAFF).count(),
                })
            stats['department_breakdown'] = department_stats
        
        return Response(stats)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def bulk_user_action(request):
    """Bulk user actions (activate, deactivate, verify, etc.)"""
    action = request.data.get('action')
    user_ids = request.data.get('user_ids', [])
    
    if not action or not user_ids:
        return Response({
            'error': 'Action and user_ids are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    users = User.objects.filter(id__in=user_ids)
    
    if action == 'activate':
        users.update(is_active=True)
        message = f'{users.count()} users activated'
    elif action == 'deactivate':
        users.update(is_active=False)
        message = f'{users.count()} users deactivated'
    elif action == 'verify':
        users.update(is_verified=True)
        message = f'{users.count()} users verified'
    elif action == 'unverify':
        users.update(is_verified=False)
        message = f'{users.count()} users unverified'
    else:
        return Response({
            'error': 'Invalid action'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({'message': message})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user(request):
    """Get current user information"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def check_email_availability(request):
    """Check if email is available for registration"""
    email = request.data.get('email')
    if not email:
        return Response({
            'error': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    is_available = not User.objects.filter(email=email).exists()
    return Response({
        'available': is_available,
        'message': 'Email is available' if is_available else 'Email is already taken'
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def check_student_id_availability(request):
    """Check if student ID is available for registration"""
    student_id = request.data.get('student_id')
    if not student_id:
        return Response({
            'error': 'Student ID is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    is_available = not User.objects.filter(student_id=student_id).exists()
    return Response({
        'available': is_available,
        'message': 'Student ID is available' if is_available else 'Student ID is already taken'
    })


class LogoutView(APIView):
    """Logout view"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({
                'message': 'Successfully logged out'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Invalid token'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserSearchView(generics.ListAPIView):
    """User search view for mentions, assignments, etc."""
    serializer_class = UserListSerializer
    permission_classes = [IsAuthorityUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['first_name', 'last_name', 'email', 'username']
    
    def get_queryset(self):
        user = self.request.user
        role_filter = self.request.query_params.get('role')
        department_filter = self.request.query_params.get('department')
        
        # Base queryset
        if user.is_admin_user or user.is_vc:
            queryset = User.objects.filter(is_active=True)
        elif user.department:
            queryset = User.objects.filter(department=user.department, is_active=True)
        else:
            queryset = User.objects.none()
        
        # Apply filters
        if role_filter:
            queryset = queryset.filter(role=role_filter)
        
        if department_filter:
            queryset = queryset.filter(department_id=department_filter)
        
        return queryset.select_related('department')[:20]  # Limit results

