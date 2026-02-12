from rest_framework import permissions
from tenants.models import Tenant


class IsSuperAdmin(permissions.BasePermission):
    """Only Super Admins pass."""

    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role_name == 'SUPER_ADMIN'
        )


class RolePermission(permissions.BasePermission):
    """
    """
    
    def _get_model_name(self, view):
        """Extract the model name from the ViewSet's queryset."""
        if hasattr(view, 'queryset') and view.queryset is not None:
            return view.queryset.model._meta.model_name
        if hasattr(view, 'get_queryset'):
            try:
                return view.get_queryset().model._meta.model_name
            except Exception:
                pass
        return None


    def _get_codename(self, view, action):
        """
        get a codename of permission thats need for this  views action  
        """
        model_name = self._get_model_name(view)
        if not model_name:
            return None

        action_map = {
            'list': f'view_{model_name}',
            'retrieve': f'view_{model_name}',
            'create': f'add_{model_name}',
            'update': f'change_{model_name}',
            'partial_update': f'change_{model_name}',
            'destroy': f'delete_{model_name}',
        }
        return action_map.get(action)

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        print("authenticated")

        # Super Admin bypasses all permission checks
        if request.user.role_name == 'SUPER_ADMIN':
            return True
        print ("not matched for issuper")
        # Safe methods (GET, HEAD, OPTIONS) — check view permission
        # Unsafe methods — check the specific action permission
        action = getattr(view, 'action', None)
        if action is None:
            # Non-ViewSet views (APIView) — just check authenticated
            return True

        codename = self._get_codename(view, action)
        if codename is None:
            # Custom actions without mapped permissions — allow for authenticated
            return True

        return request.user.has_role_perm(codename)

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Super Admin bypasses all object checks
        if user.role_name == 'SUPER_ADMIN':
            return True

        # Tenant scoping — user can only access objects in their own tenant
        if isinstance(obj, Tenant):
            if obj != user.tenant:
                return False
        elif hasattr(obj, 'tenant'):
            if obj.tenant != user.tenant:
                return False
        elif hasattr(obj, 'tenant_id'):
            if obj.tenant_id != user.tenant_id:
                return False

        return True


class ManageUser(permissions.BasePermission):

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.role_name == 'SUPER_ADMIN':
            return True

        action = getattr(view, 'action', None)
        action_map = {
            'list': 'view_user',
            'create': 'add_user',
            'update': 'change_user',
            'partial_update': 'change_user',
            'destroy': 'delete_user',
        }
        codename = action_map.get(action)
        if codename is None:
            return True

        return request.user.has_role_perm(codename)

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Super Admin can do anything
        if user.role_name == 'SUPER_ADMIN':
            return True

        # Can't edit anyone with a higher/equal admin role
        if obj.role_name == 'SUPER_ADMIN':
            return False

        # Tenant Admin specific rules
        if user.role_name == 'TENANT_ADMIN':
            if obj.tenant != user.tenant:
                return False
            return True

        # Tenant User can only access themselves
        if user.role_name == 'TENANT_USER':
            return obj == user

        # For any custom role — enforce tenant scoping
        if hasattr(obj, 'tenant') and obj.tenant != user.tenant:
            return False

        # Can't edit Tenant Admins from a custom role
        if obj.role_name == 'TENANT_ADMIN':
            return False


        return obj == user


class IsTenantAdmin(permissions.BasePermission):

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role_name in ['SUPER_ADMIN', 'TENANT_ADMIN']

    def has_object_permission(self, request, view, obj):
        if request.user.role_name == 'SUPER_ADMIN':
            return True
        if isinstance(obj, Tenant):
             return obj == request.user.tenant
        if hasattr(obj, 'tenant'):
             return obj.tenant == request.user.tenant
        if hasattr(obj, 'tenant_id'):
            return obj.tenant_id == request.user.tenant_id
        return False





