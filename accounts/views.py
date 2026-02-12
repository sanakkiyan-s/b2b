from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from .serializers import UserSerializer, UserCreateSerializer, AuditLogSerializer, RoleSerializer, PermissionSerializer
from .models import AuditLog, Role
from .permissions import ManageUser, IsSuperAdmin
from .filters import UserFilter
from tenants.models import Tenant
from courses.models import Course
from enrollments.models import Enrollment
from payments.models import Payment
from payments.models import Payment
from django.contrib.auth.models import Permission
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator

User = get_user_model()


class PermissionViewSet(viewsets.ModelViewSet):
    """CRUD for permissions — Super Admins only."""
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer

class RoleViewSet(viewsets.ModelViewSet):
    """CRUD for roles — Super Admins only."""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsSuperAdmin]
    lookup_field = 'name'


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [ManageUser]
    lookup_field = 'username'
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = UserFilter
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering_fields = ['date_joined','last_login']
    ordering = ['-date_joined']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role_name == 'SUPER_ADMIN':
            queryset = User.objects.all()
        elif user.role_name == 'TENANT_ADMIN':
            queryset = User.objects.filter(tenant=user.tenant)
        else:
            queryset = User.objects.filter(id=user.id)

        return queryset


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsSuperAdmin]

    def get_queryset(self):
        queryset = AuditLog.objects.all()
        
        # Filter by action type
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        # Filter by model name
        model_name = self.request.query_params.get('model')
        if model_name:
            queryset = queryset.filter(model_name__iexact=model_name)
        
        # Filter by user
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        return queryset


class PlatformMetricsView(APIView):
    permission_classes = [IsSuperAdmin]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'metrics'

    def get(self, request):
        now = timezone.now()
        last_7_days = now - timedelta(days=7)
        last_30_days = now - timedelta(days=30)

        # User metrics
        total_users = User.objects.count()
        active_users_7d = User.objects.filter(last_login__gte=last_7_days).count()
        users_by_role = User.objects.values('role__name').annotate(count=Count('id'))

        # Tenant metrics
        total_tenants = Tenant.objects.count()
        active_tenants = Tenant.objects.filter(is_active=True).count()

        # Course metrics
        total_courses = Course.objects.count()
        published_courses = Course.objects.filter(status='PUBLISHED').count()

        # Enrollment metrics
        total_enrollments = Enrollment.objects.count()
        enrollments_30d = Enrollment.objects.filter(enrolled_at__gte=last_30_days).count()
        completed_enrollments = Enrollment.objects.filter(status='COMPLETED').count()

        # Payment metrics
        total_payments = Payment.objects.count()
        completed_payments = Payment.objects.filter(status='COMPLETED')
        total_revenue = completed_payments.aggregate(Sum('amount'))['amount__sum'] or 0
        revenue_30d = completed_payments.filter(
            completed_at__gte=last_30_days
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        return Response({
            'users': {
                'total': total_users,
                'active_last_7_days': active_users_7d,
                'by_role': list(users_by_role),
            },
            'tenants': {
                'total': total_tenants,
                'active': active_tenants,
            },
            'courses': {
                'total': total_courses,
                'published': published_courses,
            },
            'enrollments': {
                'total': total_enrollments,
                'last_30_days': enrollments_30d,
                'completed': completed_enrollments,
            },
            'payments': {
                'total_transactions': total_payments,
                'total_revenue': float(total_revenue),
                'revenue_last_30_days': float(revenue_30d),
            },
            'generated_at': now.isoformat(),
        })


class LogoutView(APIView):
    """
    Logout user by blacklisting their refresh token.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {'message': 'Successfully logged out'},
                status=status.HTTP_205_RESET_CONTENT
            )
        except TokenError as e:
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ActivateUserView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response({'message': 'Account activated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Activation link is invalid or expired'}, status=status.HTTP_400_BAD_REQUEST)
