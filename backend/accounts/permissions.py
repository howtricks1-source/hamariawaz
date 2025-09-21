from rest_framework import permissions
from rest_framework.permissions import BasePermission


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object.
        return obj == request.user


class IsStudentUser(BasePermission):
    """
    Permission class to check if user is a student.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_student


class IsStaffUser(BasePermission):
    """
    Permission class to check if user is a staff member.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff_member


class IsDepartmentHead(BasePermission):
    """
    Permission class to check if user is a department head.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_department_head


class IsViceChancellor(BasePermission):
    """
    Permission class to check if user is a vice chancellor.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_vc


class IsAdminUser(BasePermission):
    """
    Permission class to check if user is an admin.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin_user


class IsAuthorityUser(BasePermission):
    """
    Permission class to check if user is any type of authority (staff, head, vc, admin).
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        return (
            request.user.is_staff_member or
            request.user.is_department_head or
            request.user.is_vc or
            request.user.is_admin_user
        )


class CanManageUsers(BasePermission):
    """
    Permission class to check if user can manage other users.
    Only admins can create/update/delete users.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin_user


class CanViewDepartmentData(BasePermission):
    """
    Permission class to check if user can view department-specific data.
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Admin and VC can view all department data
        if request.user.is_admin_user or request.user.is_vc:
            return True
        
        # Department heads can view their department data
        if request.user.is_department_head and request.user.department:
            return True
        
        # Staff can view their department data
        if request.user.is_staff_member and request.user.department:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Admin and VC can view all department data
        if request.user.is_admin_user or request.user.is_vc:
            return True
        
        # Users can only view data from their own department
        if hasattr(obj, 'department'):
            return obj.department == request.user.department
        
        return False


class CanAccessComplaint(BasePermission):
    """
    Permission class to check if user can access a specific complaint.
    """
    
    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        
        return request.user.can_view_complaint(obj)


class CanEditComplaint(BasePermission):
    """
    Permission class to check if user can edit a specific complaint.
    """
    
    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        
        return request.user.can_edit_complaint(obj)


class IsComplaintOwner(BasePermission):
    """
    Permission class to check if user is the owner of a complaint.
    """
    
    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        
        return obj.student == request.user


class CanAssignComplaint(BasePermission):
    """
    Permission class to check if user can assign complaints.
    Only department heads, VCs, and admins can assign complaints.
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        return (
            request.user.is_department_head or
            request.user.is_vc or
            request.user.is_admin_user
        )


class CanEscalateComplaint(BasePermission):
    """
    Permission class to check if user can escalate complaints.
    Staff can escalate to head, heads can escalate to VC.
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        return (
            request.user.is_staff_member or
            request.user.is_department_head or
            request.user.is_vc or
            request.user.is_admin_user
        )


class CanViewAnalytics(BasePermission):
    """
    Permission class to check if user can view analytics.
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # All authority users can view some level of analytics
        return (
            request.user.is_staff_member or
            request.user.is_department_head or
            request.user.is_vc or
            request.user.is_admin_user
        )


class CanViewSystemAnalytics(BasePermission):
    """
    Permission class to check if user can view system-wide analytics.
    Only VCs and admins can view system-wide analytics.
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        return request.user.is_vc or request.user.is_admin_user


class CanManageNotifications(BasePermission):
    """
    Permission class to check if user can manage notifications.
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        return (
            request.user.is_department_head or
            request.user.is_vc or
            request.user.is_admin_user
        )


class CanSendBulkNotifications(BasePermission):
    """
    Permission class to check if user can send bulk notifications.
    Only VCs and admins can send bulk notifications.
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        return request.user.is_vc or request.user.is_admin_user


# Utility functions for role-based access
def user_has_role(user, roles):
    """
    Check if user has any of the specified roles.
    
    Args:
        user: User instance
        roles: List of role strings or single role string
    
    Returns:
        bool: True if user has any of the roles
    """
    if not user or not user.is_authenticated:
        return False
    
    if isinstance(roles, str):
        roles = [roles]
    
    return user.role in roles


def user_can_access_department(user, department):
    """
    Check if user can access data from a specific department.
    
    Args:
        user: User instance
        department: Department instance
    
    Returns:
        bool: True if user can access the department
    """
    if not user or not user.is_authenticated:
        return False
    
    # Admin and VC can access all departments
    if user.is_admin_user or user.is_vc:
        return True
    
    # Users can access their own department
    return user.department == department


def get_accessible_departments(user):
    """
    Get list of departments that user can access.
    
    Args:
        user: User instance
    
    Returns:
        QuerySet: Departments that user can access
    """
    from .models import Department
    
    if not user or not user.is_authenticated:
        return Department.objects.none()
    
    # Admin and VC can access all departments
    if user.is_admin_user or user.is_vc:
        return Department.objects.filter(is_active=True)
    
    # Other users can only access their own department
    if user.department:
        return Department.objects.filter(id=user.department.id, is_active=True)
    
    return Department.objects.none()

