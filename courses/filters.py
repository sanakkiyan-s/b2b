import django_filters
from .models import Course


class CourseFilter(django_filters.FilterSet):
    """
    Filter for Course model.
    
    Usage examples:
    - /api/courses/?name=python
    - /api/courses/?status=PUBLISHED
    - /api/courses/?is_free=true
    - /api/courses/?min_price=10&max_price=100
    - /api/courses/?created_after=2026-01-01
    """
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    status = django_filters.ChoiceFilter(choices=Course.Status.choices)
    is_free = django_filters.BooleanFilter()
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Course
        fields = []  # All filters are explicitly defined above

