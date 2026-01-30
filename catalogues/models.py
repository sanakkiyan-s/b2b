from django.db import models

# Create your models here.
from courses.models import Course
from tenants.models import AbstractTenantModel
from django.utils.text import slugify


class Catalogue(AbstractTenantModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    courses = models.ManyToManyField(
        Course,
        through='CatalogueCourse',
        related_name='catalogues'
    )

    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class CatalogueCourse(AbstractTenantModel):
    catalogue = models.ForeignKey(Catalogue, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ['catalogue', 'course']

    def __str__(self):
        return f"{self.catalogue.name} - {self.course.name}"
