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
        if user is None:
            return self.none()  # No user = no results
        if user.role == 'SUPER_ADMIN':
            return self.all()  # SuperAdmin sees everything
        if user.role == 'TENANT_ADMIN' and user.tenant:
            return self.filter(tenant=user.tenant)  # TenantAdmin sees all their tenant's courses
        if user.role == 'TENANT_USER' and user.tenant:
            return self.filter(tenant=user.tenant, status='PUBLISHED') # TenantUser only sees published courses
        return self.none()


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
