from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import Course, Module, SubModule
from .serializers import CourseSerializer, ModuleSerializer, SubModuleSerializer
from accounts.permissions import IsTenantAdmin, IsTenantUser , only_tenant_admin
from drf_spectacular.utils import extend_schema, OpenApiExample
# Create your views here.


#==========Course Structure ViewSets==========

# SuperAdmin: View all courses
# TenantAdmin: Full CRUD for their tenant's courses
# TenantUser: View published courses only
class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [only_tenant_admin()]
        permission_classes = [IsTenantUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        #set_current_user(self.request.user)
        return Course.objects.for_current_user()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def modules(self, request, slug=None):
        course = self.get_object()
        modules = course.modules.all()
        serializer = ModuleSerializer(modules, many=True)
        return Response(serializer.data)

# TenantAdmin can manage modules within their courses
class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    lookup_field = 'slug'
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [only_tenant_admin()]
        permission_classes = [IsTenantUser, IsTenantAdmin]
        return [permission() for permission in permission_classes]
    def get_queryset(self):
        #set_current_user(self.request.user)
        return Module.objects.for_current_user()

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['get'])
    def submodules(self, request, slug=None):
        module = self.get_object()
        submodules = module.submodules.all()
        serializer = SubModuleSerializer(submodules, many=True)
        return Response(serializer.data)

# TenantAdmin can manage submodules within their modules
class SubModuleViewSet(viewsets.ModelViewSet):
    queryset = SubModule.objects.all()
    serializer_class = SubModuleSerializer
    lookup_field = 'slug'
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [only_tenant_admin()]
        permission_classes = [IsTenantUser, IsTenantAdmin]
        return [permission() for permission in permission_classes]
    def get_queryset(self):
        #set_current_user(self.request.user)
        return SubModule.objects.for_current_user()

    def perform_create(self, serializer):
        serializer.save()

