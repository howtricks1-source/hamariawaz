from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, NotificationPreference, NotificationBatch, EmailTemplate
from accounts.permissions import IsAdminUser, CanManageNotifications, CanSendBulkNotifications


class NotificationListView(generics.ListAPIView):
    """List user notifications"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')


class NotificationDetailView(generics.RetrieveAPIView):
    """Notification detail view"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class NotificationPreferenceListView(generics.ListAPIView):
    """List notification preferences"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)


class NotificationPreferenceUpdateView(generics.UpdateAPIView):
    """Update notification preference"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)


class BulkNotificationCreateView(generics.CreateAPIView):
    """Create bulk notification"""
    permission_classes = [CanSendBulkNotifications]
    
    def create(self, request, *args, **kwargs):
        # Placeholder implementation
        return Response({'message': 'Bulk notification functionality will be implemented'})


class NotificationBatchListView(generics.ListAPIView):
    """List notification batches"""
    permission_classes = [CanManageNotifications]
    
    def get_queryset(self):
        return NotificationBatch.objects.all().order_by('-created_at')


class NotificationBatchDetailView(generics.RetrieveAPIView):
    """Notification batch detail view"""
    permission_classes = [CanManageNotifications]
    
    def get_queryset(self):
        return NotificationBatch.objects.all()


class EmailTemplateListView(generics.ListAPIView):
    """List email templates"""
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return EmailTemplate.objects.filter(is_active=True)


class EmailTemplateDetailView(generics.RetrieveUpdateAPIView):
    """Email template detail view"""
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return EmailTemplate.objects.all()


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_read(request, pk):
    """Mark notification as read"""
    # Placeholder implementation
    return Response({'message': 'Mark read functionality will be implemented'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    # Placeholder implementation
    return Response({'message': 'Mark all read functionality will be implemented'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def unread_notification_count(request):
    """Get unread notification count"""
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return Response({'count': count})

