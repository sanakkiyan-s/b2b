from django.urls import path, include
from rest_framework_nested import routers
from .views import CourseViewSet, ModuleViewSet, SubModuleViewSet

router = routers.DefaultRouter()

router.register(r'courses', CourseViewSet)

modules_router = routers.NestedSimpleRouter(router, r'courses', lookup='course')
modules_router.register(r'modules', ModuleViewSet, basename='course-modules')

submodules_router = routers.NestedSimpleRouter(modules_router, r'modules', lookup='module')
submodules_router.register(r'submodules', SubModuleViewSet, basename='module-submodules')

#router.register(r'modules', ModuleViewSet)
#router.register(r'submodules', SubModuleViewSet)


urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    path('', include(modules_router.urls)),
    path('', include(submodules_router.urls)),
]