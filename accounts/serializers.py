from .models import AuditLog, Role
from django.contrib.auth.models import Permission
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueValidator
from tenants.models import Tenant
from skills.models import UserSkill
from .models import Role

User = get_user_model()
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from .tasks import send_invitation_email
from django.contrib.auth.password_validation import validate_password

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model=Permission
        fields='__all__'

class UserSkillsSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    class Meta:
        model = UserSkill
        fields = [
            'skill_name', 
            'proficiency', 
            'courses_completed', 

            ]
        read_only_fields= fields

class UserSerializer(serializers.ModelSerializer):
    tenant = serializers.SlugRelatedField(
        queryset=Tenant.objects.all(), 
        slug_field='slug', 
        required=False
    )
    role = serializers.SlugRelatedField(
        queryset=Role.objects.all(),
        slug_field='name',
        required=False,
        allow_null=True
    )
    get_skills = UserSkillsSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 
            'username', 
            'email', 
            'first_name', 
            'last_name', 
            'role', 
            'tenant', 
            'get_skills'
        ]
        read_only_fields = [
            'id',
            'role', 
            'tenant'
            ] 

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    tenant = serializers.SlugRelatedField(
        queryset=Tenant.objects.all(), 
        slug_field='slug', 
        required=False
    )
    role = serializers.SlugRelatedField(
        queryset=Role.objects.all(),
        slug_field='name',
        required=True
    )

    class Meta:
        model = User
        fields = [
            'email', 
            'username', 
            'password', 
            'first_name', 
            'last_name', 
            'tenant', 
            'role'
        ]

    def validate_tenant(self, value):
        request = self.context.get('request')
        if request.user.role_name == 'TENANT_ADMIN':
            if value != request.user.tenant:
                 raise serializers.ValidationError("You cannot assign a user to a different tenant.")
        return value

    def validate_role(self, value):
        request = self.context.get('request')
        user = request.user

        # Super Admin can assign any role
        if user.role_name == 'SUPER_ADMIN':
            return value

        # No one without a role can assign roles
        if not user.role:
            raise serializers.ValidationError("You do not have permission to assign roles.")

        # Prevent privilege escalation:
        # The target role's permissions must be a SUBSET of the assigner's role permissions
        assigner_perms = set(user.role.permissions.values_list('codename', flat=True))
        target_perms = set(value.permissions.values_list('codename', flat=True))

        if not target_perms.issubset(assigner_perms):
            raise serializers.ValidationError(
                "You cannot assign a role with more permissions than your own."
            )

        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        tenant = validated_data.get('tenant')
        role = validated_data.get('role')
        
        if request and request.user.tenant:
             tenant = request.user.tenant

        if role and role.name == 'SUPER_ADMIN':
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
        # Deactivate user initially
        # user.is_active = False
        # user.save()

        # Generate token and send invitation
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        activation_url = f"{settings.FRONTEND_URL}/api/activate/{uid}/{token}/"
        
        send_invitation_email.delay(
            user_email=user.email,
            first_name=user.first_name,
            activation_url=activation_url
        )

        return user



class RoleSerializer(serializers.ModelSerializer):

    permissions = serializers.DictField(write_only=True)

    class Meta:
        model = Role
        fields = ["id", "name", "description", "permissions"]


    ACTION_MAP = {
        "create": "add",
        "update": "change",
        "delete": "delete",
        "view": "view"
    }

    REVERSE_ACTION_MAP = {
        "add": "create",
        "change": "update",
        "delete": "delete",
        "view": "view"
    }


    # Convert frontend → Django Permission objects
    def create(self, validated_data):
        permissions_dict = validated_data.pop("permissions", {})
        role = Role.objects.create(**validated_data)
        self._assign_permissions(role, permissions_dict)
        return role

    def update(self, instance, validated_data):
        permissions_dict = validated_data.pop("permissions", None)
        instance = super().update(instance, validated_data)
        
        if permissions_dict is not None:
             self._assign_permissions(instance, permissions_dict)
        
        return instance

    def _assign_permissions(self, role, permissions_dict):
        """Helper to lookup and assign permissions from dict."""
        permission_objects = []
        for model_name, actions in permissions_dict.items():
            for action, allowed in actions.items():
                if allowed and action in self.ACTION_MAP:
                    django_action = self.ACTION_MAP[action]
                    codename = f"{django_action}_{model_name}"
                    try:
                        perm = Permission.objects.get(codename=codename)
                        permission_objects.append(perm)
                    except Permission.DoesNotExist:
                        pass
        role.permissions.set(permission_objects)

    # Convert Django Permission objects → frontend format
    def to_representation(self, instance):
        data = super().to_representation(instance)
        structured_permissions = {}



        for perm in instance.permissions.all():
            try:
                # Split only on the FIRST underscore to handle 'sub_module' correctly
                # add_sub_module -> "add", "sub_module"
                if "_" not in perm.codename:
                    continue
                    
                action, model = perm.codename.split("_", 1)

                if action in self.REVERSE_ACTION_MAP:
                    frontend_action = self.REVERSE_ACTION_MAP[action]

                    if model not in structured_permissions:
                        structured_permissions[model] = {
                            "create": False,
                            "update": False,
                            "delete": False,
                            "view": False
                        }

                    structured_permissions[model][frontend_action] = True
            except ValueError:
                continue

        data["permissions"] = structured_permissions
        return data

class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 
            'user', 
            'user_email', 
            'action', 
            'model_name', 
            'object_id', 
            'object_repr', 
            'details', 
            'ip_address', 
            'timestamp'
            ]
        read_only_fields = fields

class ResetPasswordEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value

class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)
    uidb64 = serializers.CharField(write_only=True)

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        try:
            uid =  force_str(urlsafe_base64_decode(attrs['uidb64']))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid UID")

        if not default_token_generator.check_token(user, attrs['token']):
             raise serializers.ValidationError("Invalid or expired token")

        attrs['user'] = user
        return attrs

    def save(self):
        password = self.validated_data['password']
        user = self.validated_data['user']
        user.set_password(password)
        user.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

class ActivateUserSerializer(serializers.Serializer):
    message = serializers.CharField(read_only=True)

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)