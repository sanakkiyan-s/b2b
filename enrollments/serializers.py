from rest_framework import serializers
from django.utils import timezone
from .models import Enrollment, SubModuleProgress
from tenants.models import Tenant
from courses.models import Course, SubModule
from django.contrib.auth import get_user_model

User = get_user_model()


class SubModuleProgressSerializer(serializers.ModelSerializer):
    submodule_title = serializers.CharField(source='submodule.title', read_only=True)
    submodule_type = serializers.CharField(source='submodule.type', read_only=True)

    class Meta:
        model = SubModuleProgress
        fields = [
            'id', 
            'enrollment', 
            'submodule', 
            'submodule_title', 
            'submodule_type',
            'is_completed', 
            'completed_at', 
            'score', 
            'time_spent'
        ]
        read_only_fields = [
            'id', 
            'completed_at', 
            'submodule_title', 
            'submodule_type'
            ]


class EnrollmentListSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_slug = serializers.CharField(source='course.slug', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    progress_percentage = serializers.ReadOnlyField()

    class Meta:
        model = Enrollment
        fields = [
            'id', 
            'user', 
            'user_email', 
            'course', 
            'course_name', 
            'course_slug',
            'status', 
            'progress_percentage', 
            'enrolled_at', 
            'completed_at'
        ]
        read_only_fields = [
            'id', 
            'enrolled_at', 
            'completed_at', 
            'progress_percentage'
            ]


class EnrollmentDetailSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_slug = serializers.CharField(source='course.slug', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    assigned_by_email = serializers.CharField(source='assigned_by.email', read_only=True, allow_null=True)
    progress_percentage = serializers.ReadOnlyField()
    submodule_progress = SubModuleProgressSerializer(many=True, read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            'id', 
            'tenant', 
            'user', 
            'user_email', 
            'course', 
            'course_name', 
            'course_slug',
            'status', 
            'progress_percentage', 
            'enrolled_at', 
            'completed_at',
            'assigned_by', 
            'assigned_by_email', 
            'submodule_progress'
        ]
        read_only_fields = fields


class EnrollmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for self-enrollment in free courses."""
    tenant = serializers.SlugRelatedField(
        queryset=Tenant.objects.all(),
        slug_field='slug',
        required=False
    )
    course = serializers.SlugRelatedField(
        queryset=Course.objects.all(),
        slug_field='slug'
    )

    class Meta:
        model = Enrollment
        fields = [
            'id', 
            'tenant', 
            'course', 
            'status', 
            'enrolled_at'
            ]
        read_only_fields = [
            'id', 
            'tenant', 
            'status', 
            'enrolled_at'
            ]

    def validate_course(self, value):
        request = self.context.get('request')
        user = request.user
#i have a doubt about super admin can enroll in the course of any tenant
        # Check tenant match
        if value.tenant != user.tenant:
            raise serializers.ValidationError("Course does not belong to your tenant.")

        # Check if course is published
        if value.status != 'PUBLISHED':
            raise serializers.ValidationError("Cannot enroll in unpublished courses.")

        # Check if course is free (for self-enrollment)
        if not value.is_free:
            raise serializers.ValidationError(
                "This is a paid course. Please complete payment first."
            )

        # Check for duplicate enrollment
        if Enrollment.objects.filter(user=user, course=value).exists():
            raise serializers.ValidationError("You are already enrolled in this course.")

        return value

    def create(self, validated_data):
        validated_data.pop('tenant', None)
        request = self.context.get('request')
        user = request.user
        return Enrollment.objects.create(
            tenant=user.tenant,
            user=user,
            **validated_data
        )


class AdminAssignCourseSerializer(serializers.Serializer):
    """Serializer for admin to assign courses to users."""
    user_email = serializers.EmailField()
    course_slug = serializers.CharField()

    def validate(self, attrs):
        request = self.context.get('request')
        admin = request.user

        # Get user
        try:
            user = User.objects.get(email=attrs['user_email'])
        except User.DoesNotExist:
            raise serializers.ValidationError({"user_email": "User not found."})

        # Get course
        try:
            course = Course.objects.get(slug=attrs['course_slug'])
        except Course.DoesNotExist:
            raise serializers.ValidationError({"course_slug": "Course not found."})

        # Check user belongs to same tenant
        if admin.role != "SUPER_ADMIN":    
            if user.tenant != admin.tenant:
                raise serializers.ValidationError({"user_email": "User does not belong to your tenant."})


        # Check course belongs to same tenant
        # if user.tenant == course.tenant:
        if admin.role != "SUPER_ADMIN":    
            if course.tenant != admin.tenant:
                raise serializers.ValidationError({"course_slug": "Course does not belong to your tenant."})


        if admin.role == "SUPER_ADMIN":
            if user.tenant != course.tenant:
                raise serializers.ValidationError({"course_slug": "Course tenant does not belong to user tenant."})
        # Check for existing enrollment
        if Enrollment.objects.filter(user=user, course=course).exists():
            raise serializers.ValidationError("User is already enrolled in this course.")

        attrs['user'] = user
        attrs['course'] = course
        return attrs


class MarkCompleteSerializer(serializers.Serializer):
    """Serializer for marking a submodule as complete."""
    score = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        allow_null=True,
        help_text="Score for assignment-type submodules (0-100)"
    )
    time_spent_seconds = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Time spent in seconds"
    )
