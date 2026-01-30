from django.db import models
from django.utils.text import slugify
from .managers import TenantAwareManager
# Create your models here.

class Tenant(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)



class AbstractTenantModel(models.Model):

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    # Default manager with tenant filtering
    objects = TenantAwareManager()

    class Meta:
        abstract = True

