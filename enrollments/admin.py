from django.contrib import admin
from .models import Enrollment, SubModuleProgress


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'status', 'tenant', 'enrolled_at', 'completed_at', 'assigned_by']
    list_filter = ['tenant', 'status', 'enrolled_at']
    search_fields = ['user__email', 'course__name']
    raw_id_fields = ['user', 'course', 'assigned_by']
    readonly_fields = ['enrolled_at']


@admin.register(SubModuleProgress)
class SubModuleProgressAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'submodule', 'is_completed', 'score', 'completed_at']
    list_filter = ['tenant', 'is_completed']
    search_fields = ['enrollment__user__email', 'submodule__title']
    raw_id_fields = ['enrollment', 'submodule']
