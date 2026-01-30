from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueValidator
from tenants.models import Tenant



User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    tenant = serializers.SlugRelatedField(
        queryset=Tenant.objects.all(), 
        slug_field='slug', 
        required=False
    )
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'tenant']
        read_only_fields = ['id', 'role', 'tenant'] 

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    tenant = serializers.SlugRelatedField(
        queryset=Tenant.objects.all(), 
        slug_field='slug', 
        required=False
    )
    role = serializers.ChoiceField(choices=User.Role.choices, required=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'first_name', 'last_name', 'tenant', 'role']

    def validate_tenant(self, value):
        request = self.context.get('request')
        if request.user.role == User.Role.TENANT_ADMIN:
            if value != request.user.tenant:
                 raise serializers.ValidationError("You cannot assign a user to a different tenant.")
        return value

    def validate_role(self, value):
        request = self.context.get('request')
        if request.user.role == User.Role.TENANT_ADMIN:
            if value == User.Role.SUPER_ADMIN:
                raise serializers.ValidationError("Tenant Admins cannot create Super Admins.")
        return value

    def validate(self, attrs):
        # if User.objects.filter(email=attrs.get('email'),tenant=attrs.get('tenant')).exists():
        #     raise serializers.ValidationError({"email": "A user with this email already exists."})

        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        tenant = validated_data.get('tenant')
        role = validated_data.get('role')
        
        if request and request.user.tenant:
             tenant = request.user.tenant

        if role == User.Role.SUPER_ADMIN:
            user = User.objects.create_superuser(
                email=validated_data['email'],
                username=validated_data['username'],
                password=validated_data['password'],
                first_name=validated_data.get('first_name', ''),
                last_name=validated_data.get('last_name', ''),
                tenant=None,
                role=role,
            )
        else:
            user = User.objects.create_user(
                email=validated_data['email'],
                username=validated_data['username'],
                password=validated_data['password'],
                first_name=validated_data.get('first_name', ''),
                last_name=validated_data.get('last_name', ''),
                tenant=tenant,
                role=role,
            )
        return user

