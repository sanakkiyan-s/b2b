from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, ModuleViewSet, SubModuleViewSet

router = DefaultRouter()

router.register(r'courses', CourseViewSet)
router.register(r'modules', ModuleViewSet)
router.register(r'submodules', SubModuleViewSet)


urlpatterns = [
    # Router URLs
    path('', include(router.urls)),

]