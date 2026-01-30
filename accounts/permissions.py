from rest_framework import permissions
from tenants.models import Tenant


class IsSuperAdmin(permissions.BasePermission):

    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'SUPER_ADMIN'
        )


class IsTenantAdmin(permissions.BasePermission):

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ['SUPER_ADMIN', 'TENANT_ADMIN']

    def has_object_permission(self, request, view, obj):
        # Super Admin can access any object
        if request.user.role == 'SUPER_ADMIN':
            return True
        # Tenant Admin can only access objects in their tenant
        if isinstance(obj, Tenant):
             return obj == request.user.tenant

        if hasattr(obj, 'tenant'):
             return obj.tenant == request.user.tenant

        if hasattr(obj, 'tenant_id'):
            return obj.tenant_id == request.user.tenant_id
        return False



class IsTenantUser(permissions.BasePermission):

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ['SUPER_ADMIN', 'TENANT_ADMIN', 'TENANT_USER']

    def has_object_permission(self, request, view, obj):
        # Super Admin bypass
        if request.user.role == 'SUPER_ADMIN':
            return True
        # Tenant-scoped check
        if hasattr(obj, 'tenant'):
            return obj.tenant == request.user.tenant

        if hasattr(obj, 'tenant_id'):
            return obj.tenant_id == request.user.tenant_id
        return True



class ManageUser(permissions.BasePermission):


    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if view.action in ['create', 'update', 'partial_update', 'destroy','list']:
            return request.user.role in ['SUPER_ADMIN', 'TENANT_ADMIN']
        return True


    def has_object_permission(self, request, view, obj):
        user = request.user
       

        if user.role == 'SUPER_ADMIN':
            return True

        if user.role == 'TENANT_ADMIN':
            if obj.role == 'SUPER_ADMIN':
                return False
            if obj.tenant != user.tenant:
                return False
            return True

        if user.role == 'TENANT_USER':
            return obj == user
