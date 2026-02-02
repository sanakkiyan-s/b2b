from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SkillViewSet, CourseSkillViewSet, UserSkillViewSet

router = DefaultRouter()
router.register(r'skills', SkillViewSet, basename='skill')
router.register(r'course-skills', CourseSkillViewSet, basename='course-skill')
router.register(r'user-skills', UserSkillViewSet, basename='user-skill')

urlpatterns = [
    path('', include(router.urls)),
]
