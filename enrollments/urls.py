from django.urls import path, include
from rest_framework_nested import routers
from .views import EnrollmentViewSet, SubModuleProgressViewSet

router = routers.DefaultRouter()
router.register(r'enrollments', EnrollmentViewSet, basename='enrollment')


# enrolled_course_router = routers.NestedSimpleRouter(router, r'enrollments', lookup='enrollment')

# enrolled_course_router.register(r'courses', SubModuleProgressViewSet, basename='submodule-progress')
router.register(r'progress', SubModuleProgressViewSet, basename='submodule-progress')

urlpatterns = [
    path('', include(router.urls)),
]
