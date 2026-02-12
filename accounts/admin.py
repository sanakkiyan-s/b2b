from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Role
# Register your models here.

User = get_user_model()


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    filter_horizontal = ('permissions',)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'role', 'tenant', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff', 'tenant')
    search_fields = ('email', 'username', 'first_name', 'last_name')
