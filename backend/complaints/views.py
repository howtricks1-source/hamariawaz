from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import Complaint, ComplaintCategory, ComplaintFile, ComplaintComment
from accounts.permissions import (
    IsStudentUser, IsAuthorityUser, CanAccessComplaint, CanEditComplaint,
    CanAssignComplaint, CanEscalateComplaint
)


class ComplaintListCreateView(generics.ListCreateAPIView):
    """List and create complaints"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'category', 'department', 'assigned_to']
    search_fields = ['title', 'description', 'complaint_number']
    ordering_fields = ['created_at', 'updated_at', 'priority']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_student:
            # Students can only see their own complaints
            return Complaint.objects.filter(student=user).select_related(
                'student', 'department', 'assigned_to', 'category'
            )
        elif user.is_admin_user or user.is_vc:
            # Admin and VC can see all complaints
            return Complaint.objects.all().select_related(
                'student', 'department', 'assigned_to', 'category'
            )
        elif user.is_department_head:
            # Department heads can see complaints in their department
            return Complaint.objects.filter(department=user.department).select_related(
                'student', 'department', 'assigned_to', 'category'
            )
        elif user.is_staff_member:
            # Staff can see complaints assigned to them or in their department
            return Complaint.objects.filter(
                models.Q(assigned_to=user) | models.Q(department=user.department)
            ).select_related('student', 'department', 'assigned_to', 'category')
        
        return Complaint.objects.none()


class ComplaintDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Complaint detail view"""
    permission_classes = [permissions.IsAuthenticated, CanAccessComplaint]
    
    def get_queryset(self):
        return Complaint.objects.select_related(
            'student', 'department', 'assigned_to', 'category'
        ).prefetch_related('comments', 'files', 'status_history')


class ComplaintCommentListCreateView(generics.ListCreateAPIView):
    """List and create complaint comments"""
    permission_classes = [permissions.IsAuthenticated, CanAccessComplaint]
    
    def get_queryset(self):
        complaint_id = self.kwargs['pk']
        complaint = get_object_or_404(Complaint, pk=complaint_id)
        
        # Check if user can access this complaint
        if not self.request.user.can_view_complaint(complaint):
            return ComplaintComment.objects.none()
        
        queryset = ComplaintComment.objects.filter(complaint=complaint)
        
        # Students can't see internal comments
        if self.request.user.is_student:
            queryset = queryset.filter(is_internal=False)
        
        return queryset.select_related('author')


class ComplaintFileListCreateView(generics.ListCreateAPIView):
    """List and create complaint files"""
    permission_classes = [permissions.IsAuthenticated, CanAccessComplaint]
    
    def get_queryset(self):
        complaint_id = self.kwargs['pk']
        complaint = get_object_or_404(Complaint, pk=complaint_id)
        
        # Check if user can access this complaint
        if not self.request.user.can_view_complaint(complaint):
            return ComplaintFile.objects.none()
        
        return ComplaintFile.objects.filter(complaint=complaint).select_related('uploaded_by')


class ComplaintFileDetailView(generics.RetrieveDestroyAPIView):
    """Complaint file detail view"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ComplaintFile.objects.select_related('complaint', 'uploaded_by')


class ComplaintStatusUpdateView(APIView):
    """Update complaint status"""
    permission_classes = [permissions.IsAuthenticated, CanEditComplaint]
    
    def post(self, request, pk):
        # Placeholder implementation
        return Response({'message': 'Status update functionality will be implemented'})


class ComplaintAssignView(APIView):
    """Assign complaint to staff"""
    permission_classes = [permissions.IsAuthenticated, CanAssignComplaint]
    
    def post(self, request, pk):
        # Placeholder implementation
        return Response({'message': 'Assignment functionality will be implemented'})


class ComplaintEscalateView(APIView):
    """Escalate complaint"""
    permission_classes = [permissions.IsAuthenticated, CanEscalateComplaint]
    
    def post(self, request, pk):
        # Placeholder implementation
        return Response({'message': 'Escalation functionality will be implemented'})


class ComplaintCategoryListView(generics.ListAPIView):
    """List complaint categories"""
    queryset = ComplaintCategory.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]


class ComplaintStatsView(APIView):
    """Complaint statistics"""
    permission_classes = [IsAuthorityUser]
    
    def get(self, request):
        # Placeholder implementation
        return Response({'message': 'Statistics functionality will be implemented'})


class MyComplaintStatsView(APIView):
    """My complaint statistics (for students)"""
    permission_classes = [IsStudentUser]
    
    def get(self, request):
        # Placeholder implementation
        return Response({'message': 'My statistics functionality will be implemented'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def download_complaint_file(request, pk):
    """Download complaint file"""
    # Placeholder implementation
    return HttpResponse('File download functionality will be implemented')
