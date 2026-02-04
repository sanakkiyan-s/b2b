from rest_framework import serializers
from .models import Skill, CourseSkill, UserSkill
from tenants.models import Tenant
from courses.models import Course


class SkillSerializer(serializers.ModelSerializer):
    """Serializer for Skill CRUD operations."""
    tenant = serializers.SlugRelatedField(
        queryset=Tenant.objects.all(),
        slug_field='slug',
        required=False
    )

    class Meta:
        model = Skill
        fields = ['id', 'tenant', 'name', 'slug', 'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'tenant', 'slug', 'created_at']

    def validate_name(self, value):
        request = self.context.get('request')
        if request and request.user.tenant:
            existing = Skill.objects.filter(name=value, tenant=request.user.tenant)
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists(): 
                raise serializers.ValidationError("Skill with this name already exists.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        tenant=validated_data.pop('tenant', None)
        if request.user.role == 'TENANT_ADMIN':
            print("setting the tenanat")
            tenant = request.user.tenant
        return Skill.objects.create(tenant=tenant, **validated_data)


class CourseSkillSerializer(serializers.ModelSerializer):
    """Serializer for associating courses with skills."""
    tenant = serializers.SlugRelatedField(
        queryset=Tenant.objects.all(),
        slug_field='slug',
        required=False
    )
    course = serializers.SlugRelatedField(
        queryset=Course.objects.all(),
        slug_field='slug'
    )
    skill = serializers.SlugRelatedField(
        queryset=Skill.objects.all(),
        slug_field='slug'
    )
    course_name = serializers.CharField(source='course.name', read_only=True)
    skill_name = serializers.CharField(source='skill.name', read_only=True)

    class Meta:
        model = CourseSkill
        fields = ['id', 'tenant', 'course', 'course_name', 'skill', 'skill_name', 'weight']
        read_only_fields = ['id', 'tenant', 'course_name', 'skill_name']

    def validate(self, attrs):
        request = self.context.get('request')
        course = attrs.get('course')
        skill = attrs.get('skill')

        # Ensure course and skill belong to the same tenant as the user
        if request and request.user.tenant:
            if course and course.tenant != request.user.tenant:
                raise serializers.ValidationError({"course": "Course does not belong to your tenant."})
            if skill and skill.tenant != request.user.tenant:
                raise serializers.ValidationError({"skill": "Skill does not belong to your tenant."})

        # Check for duplicate association
        existing = CourseSkill.objects.filter(course=course, skill=skill)
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError("This course-skill association already exists.")

        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        tenant=validated_data.pop('tenant', None)
        if request.user.role == 'TENANT_ADMIN':
            tenant = request.user.tenant
        return CourseSkill.objects.create(tenant=tenant, **validated_data)


class UserSkillSerializer(serializers.ModelSerializer):
    """Read-only serializer for user skill proficiency."""
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    skill_slug = serializers.CharField(source='skill.slug', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = UserSkill
        fields = [
            'id', 'user', 'user_email', 'skill', 'skill_name', 'skill_slug',
            'proficiency', 'courses_completed', 'last_updated'
        ]
        read_only_fields = fields  # Entirely read-only, updated by signals
