from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
from django.core.files.storage import default_storage
from django.http import HttpResponse, Http404
from django.contrib.auth import get_user_model
import mimetypes
import os

User = get_user_model()

from .models import (
    Complaint, ComplaintCategory, ComplaintComment, ComplaintResponse, 
    ComplaintForward, WithdrawalRequest, ComplaintFile, WithdrawalFile,
    ComplaintStatusHistory, Department
)
from .serializers import (
    ComplaintSerializer, ComplaintCreateSerializer, ComplaintDetailSerializer,
    ComplaintCommentSerializer, ComplaintResponseSerializer, ComplaintForwardSerializer,
    WithdrawalRequestSerializer, WithdrawalRequestCreateSerializer,
    ComplaintCategorySerializer, ComplaintFileSerializer
)
from accounts.permissions import IsStudentUser, IsStaffUser, IsDepartmentHead, IsViceChancellor, IsAdminUser

class ComplaintListView(generics.ListAPIView):
    """List complaints based on user role"""
    serializer_class = ComplaintSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Complaint.objects.select_related('student', 'category', 'department', 'assigned_to')
        
        if user.role == 'student':
            # Students can only see their own complaints
            queryset = queryset.filter(student=user)
        elif user.role == 'staff':
            # Staff can see complaints assigned to them or in their department
            queryset = queryset.filter(
                Q(assigned_to=user) | Q(department=user.department)
            )
        elif user.role == 'head':
            # Department heads can see all complaints in their department
            queryset = queryset.filter(department=user.department)
        elif user.role in ['vc', 'admin']:
            # VC and Admin can see all complaints
            pass
        else:
            queryset = queryset.none()
        
        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        priority_filter = self.request.query_params.get('priority')
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        
        category_filter = self.request.query_params.get('category')
        if category_filter:
            queryset = queryset.filter(category_id=category_filter)
        
        department_filter = self.request.query_params.get('department')
        if department_filter:
            queryset = queryset.filter(department_id=department_filter)
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) |
                Q(complaint_number__icontains=search)
            )
        
        return queryset.order_by('-created_at')

class ComplaintCreateView(generics.CreateAPIView):
    """Create a new complaint"""
    serializer_class = ComplaintCreateSerializer
    permission_classes = [IsStudentUser]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        complaint = serializer.save(student=self.request.user)
        
        # Handle file uploads
        files = self.request.FILES.getlist('files')
        for file in files:
            ComplaintFile.objects.create(
                complaint=complaint,
                file=file,
                uploaded_by=self.request.user
            )

class ComplaintDetailView(generics.RetrieveUpdateAPIView):
    """Get and update complaint details"""
    serializer_class = ComplaintDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        queryset = Complaint.objects.select_related('student', 'category', 'department', 'assigned_to')
        
        if user.role == 'student':
            queryset = queryset.filter(student=user)
        elif user.role == 'staff':
            queryset = queryset.filter(
                Q(assigned_to=user) | Q(department=user.department)
            )
        elif user.role == 'head':
            queryset = queryset.filter(department=user.department)
        elif user.role in ['vc', 'admin']:
            pass
        else:
            queryset = queryset.none()
        
        return queryset

    def perform_update(self, serializer):
        old_status = self.get_object().status
        complaint = serializer.save()
        
        # Track status changes
        if old_status != complaint.status:
            ComplaintStatusHistory.objects.create(
                complaint=complaint,
                old_status=old_status,
                new_status=complaint.status,
                changed_by=self.request.user,
                reason=self.request.data.get('status_reason', '')
            )
            
            # Set resolved_at if status is resolved
            if complaint.status == 'resolved':
                complaint.resolved_at = timezone.now()
                complaint.save()

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def forward_complaint(request):
    """Forward a complaint to another user"""
    complaint_id = request.data.get('complaint_id')
    forward_to_id = request.data.get('forward_to')
    reason = request.data.get('reason', '')
    
    try:
        complaint = Complaint.objects.get(id=complaint_id)
        forward_to_user = get_object_or_404(User, id=forward_to_id)
        
        # Check permissions
        user = request.user
        if user.role == 'student':
            return Response({'error': 'Students cannot forward complaints'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        if user.role == 'staff' and complaint.department != user.department:
            return Response({'error': 'Cannot forward complaints outside your department'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        # Create forward record
        forward = ComplaintForward.objects.create(
            complaint=complaint,
            forwarded_by=user,
            forwarded_to=forward_to_user,
            reason=reason
        )
        
        # Update complaint assignment
        complaint.assigned_to = forward_to_user
        complaint.save()
        
        serializer = ComplaintForwardSerializer(forward)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Complaint.DoesNotExist:
        return Response({'error': 'Complaint not found'}, status=status.HTTP_404_NOT_FOUND)

class ComplaintResponseCreateView(generics.CreateAPIView):
    """Add a response to a complaint"""
    serializer_class = ComplaintResponseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        complaint_id = self.kwargs.get('complaint_id')
        complaint = get_object_or_404(Complaint, id=complaint_id)
        
        # Check permissions
        user = self.request.user
        if user.role == 'student' and complaint.student != user:
            raise permissions.PermissionDenied("Cannot respond to other students' complaints")
        
        serializer.save(complaint=complaint, responder=user)

class ComplaintCommentListView(generics.ListAPIView):
    """List comments for a complaint"""
    serializer_class = ComplaintCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        complaint_id = self.kwargs.get('complaint_id')
        complaint = get_object_or_404(Complaint, id=complaint_id)
        
        # Check permissions
        user = self.request.user
        if user.role == 'student' and complaint.student != user:
            raise permissions.PermissionDenied("Cannot view other students' complaint comments")
        
        queryset = ComplaintComment.objects.filter(complaint=complaint, parent=None)
        
        # Filter internal comments for students
        if user.role == 'student':
            queryset = queryset.filter(is_internal=False)
        
        return queryset.order_by('created_at')

class ComplaintCommentCreateView(generics.CreateAPIView):
    """Add a comment to a complaint"""
    serializer_class = ComplaintCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        complaint_id = self.kwargs.get('complaint_id')
        complaint = get_object_or_404(Complaint, id=complaint_id)
        
        # Check permissions
        user = self.request.user
        if user.role == 'student' and complaint.student != user:
            raise permissions.PermissionDenied("Cannot comment on other students' complaints")
        
        serializer.save(complaint=complaint, author=user)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reply_to_comment(request, comment_id):
    """Reply to a comment"""
    parent_comment = get_object_or_404(ComplaintComment, id=comment_id)
    content = request.data.get('content')
    is_internal = request.data.get('is_internal', False)
    
    if not content:
        return Response({'error': 'Content is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check permissions
    user = request.user
    if user.role == 'student' and parent_comment.complaint.student != user:
        return Response({'error': 'Cannot reply to comments on other students\' complaints'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    reply = ComplaintComment.objects.create(
        complaint=parent_comment.complaint,
        author=user,
        content=content,
        is_internal=is_internal and user.role != 'student',  # Students cannot create internal comments
        parent=parent_comment
    )
    
    serializer = ComplaintCommentSerializer(reply)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

# Withdrawal Request Views
class WithdrawalRequestListView(generics.ListAPIView):
    """List withdrawal requests"""
    serializer_class = WithdrawalRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = WithdrawalRequest.objects.select_related('complaint', 'student', 'reviewed_by')
        
        if user.role == 'student':
            queryset = queryset.filter(student=user)
        elif user.role == 'staff':
            queryset = queryset.filter(complaint__department=user.department)
        elif user.role == 'head':
            queryset = queryset.filter(complaint__department=user.department)
        elif user.role in ['vc', 'admin']:
            pass
        else:
            queryset = queryset.none()
        
        return queryset.order_by('-created_at')

class WithdrawalRequestCreateView(generics.CreateAPIView):
    """Create a withdrawal request"""
    serializer_class = WithdrawalRequestCreateSerializer
    permission_classes = [IsStudentUser]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        withdrawal = serializer.save(student=self.request.user)
        
        # Handle file uploads
        files = self.request.FILES.getlist('files')
        for file in files:
            WithdrawalFile.objects.create(
                withdrawal_request=withdrawal,
                file=file
            )

class WithdrawalRequestDetailView(generics.RetrieveUpdateAPIView):
    """Get and update withdrawal request details"""
    serializer_class = WithdrawalRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        queryset = WithdrawalRequest.objects.select_related('complaint', 'student', 'reviewed_by')
        
        if user.role == 'student':
            queryset = queryset.filter(student=user)
        elif user.role == 'staff':
            queryset = queryset.filter(complaint__department=user.department)
        elif user.role == 'head':
            queryset = queryset.filter(complaint__department=user.department)
        elif user.role in ['vc', 'admin']:
            pass
        else:
            queryset = queryset.none()
        
        return queryset

    def perform_update(self, serializer):
        withdrawal = serializer.save(reviewed_by=self.request.user, reviewed_at=timezone.now())
        
        # If approved, update complaint status
        if withdrawal.status == 'approved':
            withdrawal.complaint.status = 'withdrawn'
            withdrawal.complaint.save()

# Utility Views
class ComplaintCategoryListView(generics.ListAPIView):
    """List complaint categories"""
    queryset = ComplaintCategory.objects.filter(is_active=True)
    serializer_class = ComplaintCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class DepartmentListView(generics.ListAPIView):
    """List departments"""
    queryset = Department.objects.all()
    serializer_class = 'DepartmentSerializer'  # Will create this
    permission_classes = [permissions.IsAuthenticated]

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def download_file(request, file_id):
    """Download complaint or withdrawal file"""
    try:
        # Try complaint file first
        try:
            file_obj = ComplaintFile.objects.get(id=file_id)
            complaint = file_obj.complaint
            
            # Check permissions
            user = request.user
            if user.role == 'student' and complaint.student != user:
                raise permissions.PermissionDenied("Cannot download files from other students' complaints")
            elif user.role == 'staff' and complaint.department != user.department:
                raise permissions.PermissionDenied("Cannot download files from other departments")
            
        except ComplaintFile.DoesNotExist:
            # Try withdrawal file
            file_obj = WithdrawalFile.objects.get(id=file_id)
            withdrawal = file_obj.withdrawal_request
            
            # Check permissions
            user = request.user
            if user.role == 'student' and withdrawal.student != user:
                raise permissions.PermissionDenied("Cannot download files from other students' withdrawals")
        
        if not default_storage.exists(file_obj.file.name):
            raise Http404("File not found")
        
        # Serve file
        file_path = file_obj.file.path
        content_type, _ = mimetypes.guess_type(file_path)
        
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{file_obj.file_name}"'
            return response
            
    except (ComplaintFile.DoesNotExist, WithdrawalFile.DoesNotExist):
        raise Http404("File not found")

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def complaint_statistics(request):
    """Get complaint statistics for dashboard"""
    user = request.user
    
    if user.role == 'student':
        complaints = Complaint.objects.filter(student=user)
    elif user.role == 'staff':
        complaints = Complaint.objects.filter(
            Q(assigned_to=user) | Q(department=user.department)
        )
    elif user.role == 'head':
        complaints = Complaint.objects.filter(department=user.department)
    elif user.role in ['vc', 'admin']:
        complaints = Complaint.objects.all()
    else:
        complaints = Complaint.objects.none()
    
    stats = {
        'total_complaints': complaints.count(),
        'pending_complaints': complaints.filter(status='pending').count(),
        'in_progress_complaints': complaints.filter(status='in_progress').count(),
        'resolved_complaints': complaints.filter(status='resolved').count(),
        'rejected_complaints': complaints.filter(status='rejected').count(),
        'withdrawn_complaints': complaints.filter(status='withdrawn').count(),
    }
    
    # Add role-specific stats
    if user.role == 'student':
        stats['my_complaints'] = complaints.count()
        stats['awaiting_response'] = complaints.filter(
            status__in=['pending', 'in_progress']
        ).count()
    elif user.role in ['staff', 'head', 'vc', 'admin']:
        stats['assigned_to_me'] = complaints.filter(assigned_to=user).count()
        stats['urgent_complaints'] = complaints.filter(is_urgent=True).count()
    
    return Response(stats)
