from django.contrib import admin
from .models import Catalogue, CatalogueCourse
# Register your models here.
class CatalogueCourseInline(admin.TabularInline):
    model = CatalogueCourse
    extra = 1

@admin.register(Catalogue)
class CatalogueAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant', 'is_active')
    list_filter = ('tenant', 'is_active')
    inlines = [CatalogueCourseInline]
