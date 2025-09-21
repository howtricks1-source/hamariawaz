from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, Department, UserProfile


class DepartmentSerializer(serializers.ModelSerializer):
    """Department serializer"""
    
    total_complaints = serializers.ReadOnlyField()
    pending_complaints = serializers.ReadOnlyField()
    resolved_complaints = serializers.ReadOnlyField()
    head_name = serializers.CharField(source='head.get_full_name', read_only=True)
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'code', 'description', 'email', 'phone',
            'office_location', 'is_active', 'head_name',
            'total_complaints', 'pending_complaints', 'resolved_complaints',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserProfileSerializer(serializers.ModelSerializer):
    """User profile serializer"""
    
    class Meta:
        model = UserProfile
        fields = [
            'email_notifications', 'sms_notifications', 'push_notifications',
            'profile_visibility', 'date_of_birth', 'address', 'emergency_contact',
            'admission_year', 'graduation_year', 'cgpa', 'join_date',
            'qualification', 'experience_years'
        ]


class UserSerializer(serializers.ModelSerializer):
    """User serializer for general use"""
    
    profile = UserProfileSerializer(read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'role', 'department', 'department_name',
            'student_id', 'semester', 'employee_id', 'designation',
            'profile_picture', 'bio', 'is_active', 'is_verified',
            'created_at', 'last_login', 'profile'
        ]
        read_only_fields = [
            'id', 'created_at', 'last_login', 'full_name', 'department_name'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }


class UserRegistrationSerializer(serializers.ModelSerializer):
    """User registration serializer (for students only)"""
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.filter(is_active=True)
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number',
            'department', 'student_id', 'semester'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'student_id': {'required': True},
            'semester': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_student_id(self, value):
        if User.objects.filter(student_id=value).exists():
            raise serializers.ValidationError("A user with this student ID already exists.")
        return value
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # Students can only register as students
        validated_data['role'] = User.Role.STUDENT
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class UserCreateSerializer(serializers.ModelSerializer):
    """User creation serializer (for admin use)"""
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'first_name', 'last_name',
            'phone_number', 'role', 'department', 'student_id', 'semester',
            'employee_id', 'designation', 'bio', 'is_active'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_student_id(self, value):
        if value and User.objects.filter(student_id=value).exists():
            raise serializers.ValidationError("A user with this student ID already exists.")
        return value
    
    def validate_employee_id(self, value):
        if value and User.objects.filter(employee_id=value).exists():
            raise serializers.ValidationError("A user with this employee ID already exists.")
        return value
    
    def validate(self, attrs):
        role = attrs.get('role')
        
        # Validate role-specific fields
        if role == User.Role.STUDENT:
            if not attrs.get('student_id'):
                raise serializers.ValidationError("Student ID is required for students.")
            if not attrs.get('semester'):
                raise serializers.ValidationError("Semester is required for students.")
        elif role in [User.Role.STAFF, User.Role.HEAD, User.Role.VC]:
            if not attrs.get('employee_id'):
                raise serializers.ValidationError("Employee ID is required for staff members.")
        
        return attrs
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """User update serializer"""
    
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number', 'department',
            'student_id', 'semester', 'employee_id', 'designation',
            'profile_picture', 'bio', 'is_active'
        ]
    
    def validate_student_id(self, value):
        if value and User.objects.filter(student_id=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("A user with this student ID already exists.")
        return value
    
    def validate_employee_id(self, value):
        if value and User.objects.filter(employee_id=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("A user with this employee ID already exists.")
        return value


class PasswordChangeSerializer(serializers.Serializer):
    """Password change serializer"""
    
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match.")
        return attrs
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer"""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add custom claims
        data['user'] = UserSerializer(self.user).data
        data['permissions'] = {
            'is_student': self.user.is_student,
            'is_staff_member': self.user.is_staff_member,
            'is_department_head': self.user.is_department_head,
            'is_vc': self.user.is_vc,
            'is_admin_user': self.user.is_admin_user,
        }
        
        return data
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims to token
        token['role'] = user.role
        token['department_id'] = user.department.id if user.department else None
        token['full_name'] = user.get_full_name()
        
        return token


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Profile update serializer"""
    
    profile = UserProfileSerializer()
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number',
            'profile_picture', 'bio', 'profile'
        ]
    
    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update profile fields
        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance


class UserListSerializer(serializers.ModelSerializer):
    """Simplified user serializer for lists"""
    
    department_name = serializers.CharField(source='department.name', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'email', 'role', 'department_name',
            'is_active', 'is_verified', 'created_at', 'last_login'
        ]

