from rest_framework_simplejwt.authentication import JWTAuthentication
from .managers import set_current_user
from django.contrib.auth.models import AnonymousUser

class TenantAwareJWTAuthentication(JWTAuthentication):


    def authenticate(self, request):
        # Allow webhook to bypass JWT check
        # print(f"DEBUG AUTH: Path={request.path}")
        # if 'payments/webhook/' in request.path:
        #     print("DEBUG AUTH: Webhook path detected, skipping JWT auth")
        #     return (AnonymousUser(), None)

        result = super().authenticate(request)
        if result is not None:
            user, token = result
            set_current_user(user)
        return result
