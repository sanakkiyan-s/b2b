from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions
from .serializers import UserSerializer, UserCreateSerializer
from .permissions import ManageUser

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [ManageUser]
    lookup_field = 'username'

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'SUPER_ADMIN':
            return User.objects.all()
        if user.role == 'TENANT_ADMIN':
            return User.objects.filter(tenant=user.tenant)

        return User.objects.filter(pk=user.pk)

        

