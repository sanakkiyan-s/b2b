from django.db import models

from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from tenants.models import AbstractTenantModel

User = get_user_model()

class Course(AbstractTenantModel):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', _('Draft')
        PUBLISHED = 'PUBLISHED', _('Published')
        ARCHIVED = 'ARCHIVED', _('Archived')

    name = models.CharField(max_length=255)
    slug = models.SlugField(blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_free = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_courses'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Module(AbstractTenantModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    slug = models.SlugField(blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.name} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class SubModule(AbstractTenantModel):
    class Type(models.TextChoices):
        VIDEO = 'VIDEO', _('Video')
        ASSIGNMENT = 'ASSIGNMENT', _('Assignment')

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='submodules')
    title = models.CharField(max_length=255)
    slug = models.SlugField(blank=True)
    type = models.CharField(max_length=20, choices=Type.choices)
    content_url = models.URLField(blank=True)  # For videos
    content_text = models.TextField(blank=True)  # For assignments
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.module.title} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

