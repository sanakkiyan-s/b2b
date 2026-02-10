from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueValidator
from .models import Tenant

User = get_user_model()

class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            'id', 
            'name', 
            'slug', 
            'created_at', 
            'is_active'
            ]
        read_only_fields = [
            'id', 
            'slug', 
            'created_at'
            ]



