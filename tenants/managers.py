from django.db import models
from threading import local

_thread_locals = local()


def get_current_user():
    return getattr(_thread_locals, 'user', None)


def set_current_user(user):
    _thread_locals.user = user


class TenantAwareQuerySet(models.QuerySet):
    def for_tenant(self, tenant):
        """Explicitly filter by a specific tenant."""
        return self.filter(tenant=tenant)
    
    def for_current_user(self):
        """Filter based on the current user's tenant (or all for SuperAdmin)."""
        user = get_current_user()
        if not user or not user.is_authenticated:
            return self.none()  # No user = no results
        if user.role_name == 'SUPER_ADMIN':
            return self.all()  # SuperAdmin sees everything
        # if user.role_name == 'TENANT_ADMIN' and user.tenant:
        #     return self.filter(tenant=user.tenant)  # TenantAdmin sees all their tenant's courses
        # if user.role_name == 'TENANT_USER' and user.tenant:
        #     return self.filter(tenant=user.tenant, status='PUBLISHED') # TenantUser only sees published courses
   
   
        # Filter by tenant
        qs = self.filter(tenant=user.tenant)

        # If user is TENANT_ADMIN, show all
        if user.role_name == 'TENANT_ADMIN':
            return qs

        # Specific logic for Course model (hide Drafts from students)
        if self.model.__name__ == 'Course':
            # Check if user has change permission for this model
            model_name = self.model._meta.model_name
            change_perm = f'change_{model_name}'
            if user.has_role_perm(change_perm):
                return qs
            return qs.filter(status='PUBLISHED')

        # Specific logic for Enrollment and Payment models
        if self.model.__name__ in ['Enrollment', 'Payment']:
            model_name = self.model._meta.model_name
            change_perm = f'change_{model_name}'
            if user.has_role_perm(change_perm):
                return qs
            return qs.filter(user=user)

        # Specific logic for SubmoduleProgress model
        if self.model.__name__ == 'SubModuleProgress':
            model_name = self.model._meta.model_name
            change_perm = f'change_{model_name}'
            if user.has_role_perm(change_perm):
                return qs
            return qs.filter(enrollment__user=user)

        # Specific logic for Catalogue model
        if self.model.__name__ == 'Catalogue':
            model_name = self.model._meta.model_name
            change_perm = f'change_{model_name}'
            if user.has_role_perm(change_perm):
                return qs
            return qs.filter(is_active=True)


        return qs


class TenantAwareManager(models.Manager):
    """
    Manager that uses TenantAwareQuerySet.
    """
    def get_queryset(self):
        return TenantAwareQuerySet(self.model, using=self._db)
    
    def for_tenant(self, tenant):
        return self.get_queryset().for_tenant(tenant)
    
    def for_current_user(self):
        return self.get_queryset().for_current_user()
