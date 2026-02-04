from rest_framework import serializers
from .models import Catalogue, CatalogueCourse
from tenants.models import Tenant
from courses.models import Course
from courses.serializers import CourseSerializer

class CatalogueSerializer(serializers.ModelSerializer):
    courses = serializers.SerializerMethodField()
    tenant = serializers.SlugRelatedField(queryset=Tenant.objects.all(), slug_field='slug', required=False)
 
    class Meta:
        model = Catalogue
        fields = ['id', 'name', 'slug', 'description', 'is_active', 'courses', 'tenant']
        read_only_fields = ['id', 'tenant']

    def get_courses(self, obj):
        published_courses = obj.courses.filter(status='PUBLISHED')
        return CourseSerializer(published_courses, many=True).data

    def validate_name(self, value):
        request = self.context.get('request')
        # Check if a catalogue with this name exists for the current user's tenant
        if request and request.user.tenant:
            if Catalogue.objects.filter(name=value, tenant=request.user.tenant).exists():
                raise serializers.ValidationError("Catalogue with this name already exists.")
        return value
    
    def create(self, validated_data):
        validated_data.pop('tenant', None)
        request = self.context.get('request')
        tenant = request.user.tenant
        catalogue = Catalogue.objects.create(tenant=tenant, **validated_data)
        return catalogue


class CatalogueCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogueCourse
        fields = ['id', 'catalogue', 'course', 'order']
        read_only_fields = ['id']

class CatalogueAddRemoveSerializer(serializers.Serializer):
    course = serializers.CharField(help_text="Name of the course")
    order = serializers.IntegerField(required=False, help_text="Order in the catalogue (for adding)")
