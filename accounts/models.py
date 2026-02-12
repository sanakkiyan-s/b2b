from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager, Permission
from django.utils.translation import gettext_lazy as _
# Create your models here.
from tenants.models import Tenant


class Role(models.Model):
    """Dynamic role model — admins can create roles at runtime."""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name='roles',
        help_text='Permissions granted to this role.'
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def has_perm(self, codename):
        """Check if this role has a specific permission by codename."""
        return self.permissions.filter(codename=codename).exists()

class UserManager(BaseUserManager):

    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        if not username:
            raise ValueError(_('The Username field must be set'))
            
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        # Auto-assign SUPER_ADMIN role if not provided
        if 'role' not in extra_fields or extra_fields['role'] is None:
            role_obj, _ = Role.objects.get_or_create(name='SUPER_ADMIN', defaults={'description': 'Super Admin'})
            extra_fields['role'] = role_obj
        elif isinstance(extra_fields['role'], str):
            role_obj, _ = Role.objects.get_or_create(name=extra_fields['role'], defaults={'description': extra_fields['role']})
            extra_fields['role'] = role_obj

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE, 
        related_name='users', 
        null=True, 
        blank=True
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )

    @property
    def role_name(self):
        print(self.role.name)
        return self.role.name if self.role else ''

    def has_role_perm(self, codename):
        """Check if user's role grants a specific permission codename.
        Super Admins bypass all checks.
        """
        if not self.role:
            return False
        if self.role.name == 'SUPER_ADMIN':
            return True
        return self.role.has_perm(codename)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username'] 

    def __str__(self):
        return self.email

    @property
    def get_skills(self):
        return self.user_skills.all()


class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = 'CREATE', _('Create')
        UPDATE = 'UPDATE', _('Update')
        DELETE = 'DELETE', _('Delete')
        LOGIN = 'LOGIN', _('Login')
        LOGOUT = 'LOGOUT', _('Logout')

    user = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, null=True, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    details = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name} - {self.timestamp}"
