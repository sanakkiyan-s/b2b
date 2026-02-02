from django.contrib import admin
from .models import Skill, CourseSkill, UserSkill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'tenant', 'is_active', 'created_at']
    list_filter = ['tenant', 'is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(CourseSkill)
class CourseSkillAdmin(admin.ModelAdmin):
    list_display = ['course', 'skill', 'weight', 'tenant']
    list_filter = ['tenant', 'skill']
    search_fields = ['course__name', 'skill__name']


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ['user', 'skill', 'proficiency', 'courses_completed', 'last_updated']
    list_filter = ['tenant', 'skill']
    search_fields = ['user__email', 'skill__name']
    readonly_fields = ['proficiency', 'courses_completed', 'last_updated']
