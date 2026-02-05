from rest_framework_simplejwt.authentication import JWTAuthentication
from .managers import set_current_user
from django.contrib.auth.models import AnonymousUser
from accounts.signals import set_current_request
class TenantAwareJWTAuthentication(JWTAuthentication):


    def authenticate(self, request):
        result = super().authenticate(request)
        set_current_request(request)
        if result is not None:
            user, token = result
            set_current_user(user)
        return result
