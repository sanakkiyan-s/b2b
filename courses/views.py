from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import Course, Module, SubModule
from django.db.models import Exists, OuterRef, Count,Q
from .serializers import CourseSerializer, ModuleSerializer, SubModuleSerializer
from accounts.permissions import IsTenantAdmin, IsTenantUser , only_tenant_admin
from enrollments.models import Enrollment
from drf_spectacular.utils import extend_schema, OpenApiExample
from .pagination import StandardResultsSetPagination
from .filters import CourseFilter
# Create your views here.


#==========Course Structure ViewSets==========

# SuperAdmin: View all courses
# TenantAdmin: Full CRUD for their tenant's courses
# TenantUser: View published courses only

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    pagination_class = StandardResultsSetPagination
    lookup_field = 'slug'
    
    # Search, Filter, and Ordering
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CourseFilter
    search_fields = ['name', 'description']  # ?search=python
    ordering_fields = ['name', 'created_at', 'price']  # ?ordering=-created_at
    ordering = ['-created_at']  # Default ordering

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [only_tenant_admin()]
        permission_classes = [IsTenantUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        #set_current_user(self.request.user)
        queryset = Course.objects.for_current_user()#.exclude(enrollments__user=self.request.user)
        queryset = queryset.annotate(
            enrolled=Exists(Enrollment.objects.filter(user=self.request.user.id,course=OuterRef('pk'))),
            total_enrollments=Count('enrollments')
            )
        if self.request.query_params.get('enrolled')=='true':
            queryset = queryset.filter(enrollments__user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)



# TenantAdmin can manage modules within their courses
class ModuleViewSet(viewsets.ModelViewSet):
    serializer_class = ModuleSerializer
    pagination_class = StandardResultsSetPagination
    lookup_field = 'slug'
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [only_tenant_admin()]
        permission_classes = [IsTenantUser, IsTenantAdmin]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self): 
        if self.request.user.is_superuser:
            return Module.objects.filter(
                course__slug=self.kwargs['course_slug'], # Matches lookup='course' in urls.py
            ).annotate(submodule_count=Count('submodules'),submodule_completed=Count('submodules__user_progress',filter=Q(submodules__user_progress__is_completed=True,
            submodules__user_progress__enrollment__user=self.request.user)) or 0)
        return Module.objects.filter(
            course__slug=self.kwargs['course_slug'], # Matches lookup='course' in urls.py
            course__tenant=self.request.user.tenant,
            tenant=self.request.user.tenant 
        ).annotate(submodule_count=Count('submodules'),submodule_completed=Count('submodules__user_progress',filter=Q(submodules__user_progress__is_completed=True,
            submodules__user_progress__enrollment__user=self.request.user)) or 0)

    def perform_create(self, serializer):
        serializer.save()


# TenantAdmin can manage submodules within their modules
class SubModuleViewSet(viewsets.ModelViewSet):
    queryset = SubModule.objects.all()
    serializer_class = SubModuleSerializer
    pagination_class = StandardResultsSetPagination
    lookup_field = 'slug'
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsTenantAdmin()]
        permission_classes = [IsTenantUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):

        if self.request.user.is_superuser:
            return SubModule.objects.filter(
                module__course__slug=self.kwargs['course_slug'],
                module__slug=self.kwargs['module_slug'],
            )
        return SubModule.objects.filter(
            module__course__slug=self.kwargs['course_slug'],
            module__course__tenant=self.request.user.tenant,
            module__slug=self.kwargs['module_slug'], 
            tenant=self.request.user.tenant 
        )

    def perform_create(self, serializer):
        serializer.save()

