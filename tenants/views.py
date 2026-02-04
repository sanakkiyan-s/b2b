from django.shortcuts import render
from rest_framework import viewsets
from .models import Tenant
from .serializers import TenantSerializer
from accounts.permissions import IsSuperAdmin, IsTenantAdmin
# Create your views here.
# super admin can View all tenants
# tenant admin can view only their own tenant
class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    lookup_field = 'slug'

    def get_permissions(self):
  
        if self.action in ['list', 'create', 'destroy']:
            permission_classes = [IsSuperAdmin]
        else:
            permission_classes = [IsTenantAdmin]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'SUPER_ADMIN':
            return Tenant.objects.all()
        elif user.role == 'TENANT_ADMIN' and user.tenant:
            return Tenant.objects.filter(slug=user.tenant.slug)
        return Tenant.objects.none()

