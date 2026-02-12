from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from .models import AuditLog, User
from tenants.models import Tenant
from courses.models import Course, Module, SubModule
from catalogues.models import Catalogue
from skills.models import Skill, CourseSkill, UserSkill
from enrollments.models import Enrollment
from payments.models import Payment
import threading
from django.dispatch import receiver
from django.urls import reverse
from .tasks import send_password_reset_email

from django_rest_passwordreset.signals import reset_password_token_created


def get_client_ip(request):
    if request is None:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


# Thread-local storage to pass request to signals
_thread_locals = threading.local()
def set_current_request(request):
    _thread_locals.request = request


def get_current_request():
    return getattr(_thread_locals, 'request', None)

def get_current_user():
    request = get_current_request()
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        return request.user
    return None


def create_audit_log(action, model_name, instance, user=None):
    if user is None:
        user = get_current_user()
    
    if user and user.role_name not in ['SUPER_ADMIN', 'TENANT_ADMIN']:
        return
    
    request = get_current_request()
    ip_address = get_client_ip(request) if request else None
    
    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=str(instance.pk),
        object_repr=str(instance),
        ip_address=ip_address
    )


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    if user.role_name in ['SUPER_ADMIN', 'TENANT_ADMIN']:
        AuditLog.objects.create(
            user=user,
            action=AuditLog.Action.LOGIN,
            model_name='User',
            object_id=str(user.pk),
            object_repr=str(user),
            ip_address=get_client_ip(request)
        )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user and user.role_name in ['SUPER_ADMIN', 'TENANT_ADMIN']:
        AuditLog.objects.create(
            user=user,
            action=AuditLog.Action.LOGOUT,
            model_name='User',
            object_id=str(user.pk),
            object_repr=str(user),
            ip_address=get_client_ip(request)
        )


# Model signals for key models
AUDITED_MODELS = [
    # Core
    (Tenant, 'Tenant'),
    (User, 'User'),
    # Courses
    (Course, 'Course'),
    (Module, 'Module'),
    (SubModule, 'SubModule'),
    # Catalogues
    (Catalogue, 'Catalogue'),
    # Skills
    (Skill, 'Skill'),
    (CourseSkill, 'CourseSkill'),
    (UserSkill, 'UserSkill'),
    # Enrollments 
    (Enrollment, 'Enrollment'),
    # Payments
    (Payment, 'Payment'),
]

for model_class, model_name in AUDITED_MODELS:
    def make_create_handler(m_name):
        def handler(sender, instance, created, **kwargs):
            if created:
                create_audit_log(AuditLog.Action.CREATE, m_name, instance)
        return handler
    
    def make_delete_handler(m_name):
        def handler(sender, instance, **kwargs):
            create_audit_log(AuditLog.Action.DELETE, m_name, instance)
        return handler
    
    post_save.connect(make_create_handler(model_name), sender=model_class, weak=False)
    post_delete.connect(make_delete_handler(model_name), sender=model_class, weak=False)



@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    """
    Handles password reset tokens
    When a token is created, an e-mail needs to be sent to the user
    :param sender: View Class that sent the signal
    :param instance: View Instance that sent the signal
    :param reset_password_token: Token Model Object
    :param args:
    :param kwargs:
    :return:
    """
    
    # send an e-mail to the user
    task_context = {
        'username': reset_password_token.user.username,
        'email': reset_password_token.user.email,
        'reset_password_url': "{}?token={}".format(
            instance.request.build_absolute_uri(reverse('password_reset:reset-password-confirm')),
            reset_password_token.key)
    }
    
    send_password_reset_email.delay(reset_password_token.user.email, task_context)