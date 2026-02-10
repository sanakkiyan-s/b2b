from rest_framework import viewsets
from rest_framework.response import Response
from .models import Skill, CourseSkill, UserSkill
from .serializers import SkillSerializer, CourseSkillSerializer, UserSkillSerializer
from accounts.permissions import IsTenantAdmin, IsTenantUser


class SkillViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Skills.
    - TenantAdmin: Full CRUD
    - TenantUser: Read-only access
    - SuperAdmin: Access all skills
    """
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsTenantAdmin()]
        return [IsTenantUser()]

    def get_queryset(self):
        return Skill.objects.for_current_user()


class CourseSkillViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Course-Skill associations.
    - TenantAdmin: Full CRUD
    - TenantUser: Read-only access
    - SuperAdmin: Access all associations
    """

    queryset = CourseSkill.objects.all()
    serializer_class = CourseSkillSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsTenantAdmin()]
        return [IsTenantUser()]

    def get_queryset(self):
        return CourseSkill.objects.for_current_user()


class UserSkillViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing User Skill proficiency (read-only).
    - TenantUser: View own skills
    - TenantAdmin: View all users' skills in tenant
    - SuperAdmin: View all user skills
    """
    queryset = UserSkill.objects.all()
    serializer_class = UserSkillSerializer

    def get_permissions(self):
        return [IsTenantUser()]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'SUPER_ADMIN':
            return UserSkill.objects.all()
        if user.role == 'TENANT_ADMIN' and user.tenant:
            return UserSkill.objects.filter(tenant=user.tenant)
        if user.role == 'TENANT_USER' and user.tenant:
            return UserSkill.objects.filter(user=user, tenant=user.tenant)
        return UserSkill.objects.none()
