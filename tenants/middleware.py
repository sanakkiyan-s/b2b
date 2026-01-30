from rest_framework_simplejwt.authentication import JWTAuthentication
from .managers import set_current_user


class CurrentUserMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        
        # taking the bearer token from the header even if the user is authenticated by session using admin page 
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if auth_header and 'Bearer' in auth_header:
            try:
                jwt_auth = JWTAuthentication()
               # print("JWT Authentication")
               # print(jwt_auth)
                auth_result = jwt_auth.authenticate(request)
               # print(auth_result)
                if auth_result:
                    user = auth_result[0]
                    request.user = user
            except Exception:
                # If JWT fails, we just fall back to whatever (or nothing)
                pass

        if user and user.is_authenticated:
           # print("Setting current user")
           # print(user)
            set_current_user(user)
        else:
           # print("Setting current user to None")
            set_current_user(None)
        
        response = self.get_response(request)
        
        # Clean up after request
        print("Cleaning up...")
        set_current_user(None)
        return response
