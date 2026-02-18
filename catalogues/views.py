from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample
from .models import Catalogue, Course
from .serializers import CatalogueSerializer, CourseSerializer, CatalogueAddRemoveSerializer
from accounts.permissions import RolePermission 
from django.db.models import Max
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your views here.

# TenantAdmin manages catalogues
class CatalogueViewSet(viewsets.ModelViewSet):
    queryset = Catalogue.objects.all()
    serializer_class = CatalogueSerializer
    lookup_field = 'slug'

    def get_permissions(self):
        permission_classes = [RolePermission]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        return Catalogue.objects.for_current_user().select_related('tenant')


    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['get'])
    def courses(self, request, slug=None):
        catalogue = self.get_object()
        courses = catalogue.courses.filter(status='PUBLISHED').select_related('created_by')
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=CatalogueAddRemoveSerializer,
        responses={200: {'description': 'Course added successfully'}}
    )
    @action(detail=True, methods=['post'])
    def add_course(self, request, slug=None):
        catalogue = self.get_object()
        try:
            course_name = request.data.get('course')
            course = Course.objects.get(name=course_name)
        except Course.DoesNotExist:
            return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
            
        order = request.data.get('order')
        if order is None:
             current_max = catalogue.cataloguecourse_set.aggregate(Max('order'))['order__max']
             order = (current_max or 0) + 1
    
        catalogue.courses.add(course, through_defaults={'order': order, 'tenant': catalogue.tenant})
        return Response({'message': 'Course added successfully'} , status=status.HTTP_200_OK)

    @extend_schema(
        request=CatalogueAddRemoveSerializer,
        examples=[
            OpenApiExample(
                'Remove Course Example',
                value={'course': 'Advanced Microservices Patterns'},
                request_only=True,
            )
        ],
        responses={200: {'description': 'Course removed successfully'}}
    )
    @action(detail=True, methods=['delete'])
    def remove_course(self, request, slug=None):
        catalogue = self.get_object()
        try:
            course_slug = request.data.get('course_slug')
            course = Course.objects.get(slug=course_slug)
        except Course.DoesNotExist:
            return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if not catalogue.courses.filter(id=course.id).exists():
             return Response({'error': 'Course is not in this catalogue'}, status=status.HTTP_400_BAD_REQUEST)

        catalogue.courses.remove(course)
        return Response({'message': 'Course removed successfully'})