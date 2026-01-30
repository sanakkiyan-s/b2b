from django.contrib import admin
from .models import Course, Module, SubModule
# Register your models here.

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant', 'status', 'is_free', 'price', 'created_at')
    list_filter = ('tenant', 'status', 'is_free')
    search_fields = ('name', 'tenant__name')

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'tenant', 'order')
    list_filter = ('tenant', 'course')
    search_fields = ('title', 'course__name')

@admin.register(SubModule)
class SubModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'type', 'tenant', 'order')
    list_filter = ('tenant', 'type', 'module__course')
    search_fields = ('title', 'module__title')


