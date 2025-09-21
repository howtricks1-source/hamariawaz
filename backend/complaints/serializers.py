from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Complaint, ComplaintCategory, ComplaintComment, ComplaintResponse,
    ComplaintForward, WithdrawalRequest, ComplaintFile, WithdrawalFile,
    ComplaintStatusHistory, Department
)

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for nested serialization"""
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'role']

class DepartmentSerializer(serializers.ModelSerializer):
    """Department serializer"""
    head_name = serializers.CharField(source='head.full_name', read_only=True)
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'description', 'head', 'head_name']

class ComplaintCategorySerializer(serializers.ModelSerializer):
    """Complaint category serializer"""
    
    class Meta:
        model = ComplaintCategory
        fields = ['id', 'name', 'description', 'color', 'is_active']

class ComplaintFileSerializer(serializers.ModelSerializer):
    """Complaint file serializer"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.full_name', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ComplaintFile
        fields = [
            'id', 'file', 'file_name', 'file_size', 'file_type',
            'uploaded_by', 'uploaded_by_name', 'uploaded_at', 'file_url'
        ]
        read_only_fields = ['file_name', 'file_size', 'file_type', 'uploaded_by', 'uploaded_at']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(f'/api/complaints/files/{obj.id}/download/')
        return None

class ComplaintCommentSerializer(serializers.ModelSerializer):
    """Complaint comment serializer"""
    author_name = serializers.CharField(source='author.full_name', read_only=True)
    author_role = serializers.CharField(source='author.role', read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = ComplaintComment
        fields = [
            'id', 'content', 'is_internal', 'author', 'author_name', 'author_role',
            'created_at', 'updated_at', 'replies'
        ]
        read_only_fields = ['author', 'created_at', 'updated_at']
    
    def get_replies(self, obj):
        if obj.replies.exists():
            return ComplaintCommentSerializer(
                obj.replies.all(), 
                many=True, 
                context=self.context
            ).data
        return []

class ComplaintResponseSerializer(serializers.ModelSerializer):
    """Complaint response serializer"""
    responder_name = serializers.CharField(source='responder.full_name', read_only=True)
    responder_role = serializers.CharField(source='responder.role', read_only=True)
    
    class Meta:
        model = ComplaintResponse
        fields = [
            'id', 'content', 'is_final_response', 'responder', 'responder_name',
            'responder_role', 'created_at'
        ]
        read_only_fields = ['responder', 'created_at']

class ComplaintForwardSerializer(serializers.ModelSerializer):
    """Complaint forward serializer"""
    forwarded_by_name = serializers.CharField(source='forwarded_by.full_name', read_only=True)
    forwarded_to_name = serializers.CharField(source='forwarded_to.full_name', read_only=True)
    
    class Meta:
        model = ComplaintForward
        fields = [
            'id', 'reason', 'forwarded_by', 'forwarded_by_name',
            'forwarded_to', 'forwarded_to_name', 'created_at'
        ]
        read_only_fields = ['forwarded_by', 'created_at']

class ComplaintStatusHistorySerializer(serializers.ModelSerializer):
    """Complaint status history serializer"""
    changed_by_name = serializers.CharField(source='changed_by.full_name', read_only=True)
    
    class Meta:
        model = ComplaintStatusHistory
        fields = [
            'id', 'old_status', 'new_status', 'reason', 'changed_by',
            'changed_by_name', 'created_at'
        ]

class ComplaintSerializer(serializers.ModelSerializer):
    """Basic complaint serializer for list views"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.full_name', read_only=True)
    days_since_created = serializers.SerializerMethodField()
    
    class Meta:
        model = Complaint
        fields = [
            'id', 'complaint_number', 'title', 'description', 'status', 'priority',
            'student', 'student_name', 'student_id', 'category', 'category_name',
            'category_color', 'department', 'department_name', 'assigned_to',
            'assigned_to_name', 'is_anonymous', 'is_urgent', 'created_at',
            'updated_at', 'resolved_at', 'due_date', 'days_since_created'
        ]
    
    def get_days_since_created(self, obj):
        from django.utils import timezone
        delta = timezone.now() - obj.created_at
        return delta.days

class ComplaintDetailSerializer(serializers.ModelSerializer):
    """Detailed complaint serializer"""
    student = UserBasicSerializer(read_only=True)
    category = ComplaintCategorySerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    assigned_to = UserBasicSerializer(read_only=True)
    files = ComplaintFileSerializer(many=True, read_only=True)
    comments = ComplaintCommentSerializer(many=True, read_only=True)
    responses = ComplaintResponseSerializer(many=True, read_only=True)
    forwards = ComplaintForwardSerializer(many=True, read_only=True)
    status_history = ComplaintStatusHistorySerializer(many=True, read_only=True)
    days_since_created = serializers.SerializerMethodField()
    
    class Meta:
        model = Complaint
        fields = [
            'id', 'complaint_number', 'title', 'description', 'status', 'priority',
            'student', 'category', 'department', 'assigned_to', 'is_anonymous',
            'is_urgent', 'created_at', 'updated_at', 'resolved_at', 'due_date',
            'files', 'comments', 'responses', 'forwards', 'status_history',
            'days_since_created'
        ]
        read_only_fields = [
            'id', 'complaint_number', 'student', 'created_at', 'updated_at'
        ]
    
    def get_days_since_created(self, obj):
        from django.utils import timezone
        delta = timezone.now() - obj.created_at
        return delta.days

class ComplaintCreateSerializer(serializers.ModelSerializer):
    """Complaint creation serializer"""
    files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Complaint
        fields = [
            'title', 'description', 'category', 'department', 'priority',
            'is_anonymous', 'is_urgent', 'files'
        ]
    
    def validate(self, data):
        # Ensure category belongs to the selected department if both are provided
        if data.get('category') and data.get('department'):
            # Add validation logic if categories are department-specific
            pass
        return data

class WithdrawalFileSerializer(serializers.ModelSerializer):
    """Withdrawal file serializer"""
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = WithdrawalFile
        fields = [
            'id', 'file', 'file_name', 'file_size', 'file_type',
            'uploaded_at', 'file_url'
        ]
        read_only_fields = ['file_name', 'file_size', 'file_type', 'uploaded_at']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(f'/api/complaints/files/{obj.id}/download/')
        return None

class WithdrawalRequestSerializer(serializers.ModelSerializer):
    """Withdrawal request serializer"""
    student = UserBasicSerializer(read_only=True)
    complaint_number = serializers.CharField(source='complaint.complaint_number', read_only=True)
    complaint_title = serializers.CharField(source='complaint.title', read_only=True)
    reviewed_by = UserBasicSerializer(read_only=True)
    files = WithdrawalFileSerializer(many=True, read_only=True)
    
    class Meta:
        model = WithdrawalRequest
        fields = [
            'id', 'complaint', 'complaint_number', 'complaint_title', 'student',
            'reason', 'status', 'reviewed_by', 'review_notes', 'created_at',
            'reviewed_at', 'files'
        ]
        read_only_fields = [
            'id', 'student', 'reviewed_by', 'created_at', 'reviewed_at'
        ]

class WithdrawalRequestCreateSerializer(serializers.ModelSerializer):
    """Withdrawal request creation serializer"""
    files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = WithdrawalRequest
        fields = ['complaint', 'reason', 'files']
    
    def validate_complaint(self, value):
        # Ensure the complaint belongs to the requesting student
        request = self.context.get('request')
        if request and request.user.role == 'student':
            if value.student != request.user:
                raise serializers.ValidationError("You can only request withdrawal for your own complaints")
        
        # Ensure complaint doesn't already have a withdrawal request
        if hasattr(value, 'withdrawal_request'):
            raise serializers.ValidationError("This complaint already has a withdrawal request")
        
        # Ensure complaint is not already resolved or withdrawn
        if value.status in ['resolved', 'withdrawn']:
            raise serializers.ValidationError("Cannot request withdrawal for resolved or withdrawn complaints")
        
        return value

# Additional serializers for specific endpoints
class ComplaintAssignSerializer(serializers.Serializer):
    """Serializer for assigning complaints"""
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    reason = serializers.CharField(max_length=500, required=False)

class ComplaintStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating complaint status"""
    status = serializers.ChoiceField(choices=Complaint.STATUS_CHOICES)
    reason = serializers.CharField(max_length=500, required=False)

class ComplaintForwardCreateSerializer(serializers.Serializer):
    """Serializer for forwarding complaints"""
    complaint_id = serializers.UUIDField()
    forward_to = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    reason = serializers.CharField(max_length=500)

class BulkActionSerializer(serializers.Serializer):
    """Serializer for bulk actions on complaints"""
    complaint_ids = serializers.ListField(child=serializers.UUIDField())
    action = serializers.ChoiceField(choices=['assign', 'status_update', 'priority_update'])
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    status = serializers.ChoiceField(choices=Complaint.STATUS_CHOICES, required=False)
    priority = serializers.ChoiceField(choices=Complaint.PRIORITY_CHOICES, required=False)
    reason = serializers.CharField(max_length=500, required=False)

