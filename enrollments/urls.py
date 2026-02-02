from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EnrollmentViewSet, SubModuleProgressViewSet

router = DefaultRouter()
router.register(r'enrollments', EnrollmentViewSet, basename='enrollment')
router.register(r'progress', SubModuleProgressViewSet, basename='submodule-progress')

urlpatterns = [
    path('', include(router.urls)),
]
