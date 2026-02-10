import django_filters
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFilter(django_filters.FilterSet):
    """
    examples:
    - /api/users/?search=john
    - /api/users/?role=TENANT_USER
    - /api/users/?is_active=true
    - /api/users/?joined_after=2026-01-01
    """
    email = django_filters.CharFilter(lookup_expr='icontains')
    username = django_filters.CharFilter(lookup_expr='icontains')
    first_name = django_filters.CharFilter(lookup_expr='icontains')
    last_name = django_filters.CharFilter(lookup_expr='icontains')
    role = django_filters.ChoiceFilter(choices=User.Role.choices)
    is_active = django_filters.BooleanFilter()
    tenant = django_filters.CharFilter(field_name='tenant__slug', lookup_expr='exact')
    joined_after = django_filters.DateFilter(field_name='date_joined', lookup_expr='gte')
    joined_before = django_filters.DateFilter(field_name='date_joined', lookup_expr='lte')
    last_login_after = django_filters.DateTimeFilter(field_name='last_login', lookup_expr='gte')
    last_login_before = django_filters.DateTimeFilter(field_name='last_login', lookup_expr='lte')
    skills = django_filters.CharFilter(field_name='user_skills__skill__name', lookup_expr='icontains')
    class Meta:
        model = User
        fields = [] 
