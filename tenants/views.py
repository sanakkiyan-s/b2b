from django.shortcuts import render
from rest_framework import viewsets
from .models import Tenant
from .serializers import TenantSerializer
from accounts.permissions import IsSuperAdmin, RolePermission
# Create your views here.
# super admin can View all tenants
# tenant admin can view only their own tenant
class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    lookup_field = 'slug'

    def get_permissions(self):
  
        if self.action == 'create':
            permission_classes = [IsSuperAdmin]
        else:
            permission_classes = [RolePermission]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.role_name == 'SUPER_ADMIN':
            return Tenant.objects.all()
        elif user.role_name == 'TENANT_ADMIN' and user.tenant:
            return Tenant.objects.filter(slug=user.tenant.slug)
        return Tenant.objects.none()

