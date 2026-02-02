from rest_framework import serializers
from .models import Course, Module, SubModule
from tenants.models import Tenant
# ==================== Course Structure Serializers ====================

class SubModuleSerializer(serializers.ModelSerializer):
    tenant = serializers.SlugRelatedField(queryset=Tenant.objects.all(), slug_field='slug', required=False)
    module = serializers.SlugRelatedField(queryset=Module.objects.all(), slug_field='slug', required=False)
    class Meta:
        model = SubModule
        fields = ['id', 'tenant', 'module', 'title', 'slug', 'type', 'content_url', 'content_text', 'order']
        read_only_fields = ['id', 'tenant', 'slug']

    def validate_title(self, value):
        request = self.context.get('request')
        module_slug = self.initial_data.get('module')
        
        if module_slug:
            if SubModule.objects.filter(module__slug=module_slug, title=value).exists():
                raise serializers.ValidationError("SubModule with this title already exists in this module.")
        return value

    def create(self, validated_data):
        validated_data.pop('tenant', None)
        request = self.context.get('request')
        tenant = request.user.tenant
        sub_module = SubModule.objects.create(tenant=tenant, **validated_data)
        return sub_module

class ModuleSerializer(serializers.ModelSerializer):
    submodules = SubModuleSerializer(many=True, read_only=True)
    tenant = serializers.SlugRelatedField(queryset=Tenant.objects.all(), slug_field='slug', required=False)
    course = serializers.SlugRelatedField(queryset=Course.objects.all(), slug_field='slug', required=False)
    class Meta:
        model = Module
        fields = ['id', 'tenant', 'course', 'title', 'slug', 'description', 'order','submodules']
        read_only_fields = ['id', 'tenant', 'slug']

    def validate_title(self, value):
        # Check uniqueness within the course
        course_slug = self.initial_data.get('course')
        if course_slug:
             if Module.objects.filter(course__slug=course_slug, title=value).exists():
                 raise serializers.ValidationError("Module with this title already exists in this course.")
        return value

    def create(self, validated_data):
        validated_data.pop('tenant', None)
        request = self.context.get('request')
        tenant = request.user.tenant
        module = Module.objects.create(tenant=tenant, **validated_data)
        return module

class CourseSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)
    created_by = serializers.CharField(source='created_by.username', read_only=True)
    tenant = serializers.SlugRelatedField(queryset=Tenant.objects.all(), slug_field='slug', required=False)
    class Meta:
        model = Course
        fields = [
            'id', 'tenant', 'name','slug', 'description', 'price', 'is_free', 
            'status', 'created_by', 
            'created_at', 'updated_at', 'modules'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'slug']

    def validate_name(self, value):
        request = self.context.get('request')
        if request and request.user.tenant:
            if Course.objects.filter(name=value, tenant=request.user.tenant).exists():
                raise serializers.ValidationError("Course with this name already exists.")
        return value
    
    def create(self, validated_data):
        # Remove 'tenant' from validated_data if present, as we force it from the user
        validated_data.pop('tenant', None)
        
        request = self.context.get('request')
        tenant = request.user.tenant
        course = Course.objects.create(tenant=tenant, **validated_data)
        return course

