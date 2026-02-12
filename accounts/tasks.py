from celery import shared_task
import time
import socket

from datetime import datetime
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

@shared_task
def print_every_minute():
    print(f"[CELERY BEAT] 1 minute exceeded at {datetime.now()}")
    return "Printed successfully"

# Email task
@shared_task(queue="email_queue")
def send_email(email, seconds):
    worker = socket.gethostname()
    print(f"[EMAIL TASK] Worker: {worker} | Sending email to {email}")
    
    time.sleep(seconds)
    
    print(f"[EMAIL TASK DONE] Worker: {worker} | Email sent to {email}")
    
    return f"Email sent to {email}"


# Default task
@shared_task(queue="default_queue")
def generate_report(report_id, seconds):
    worker = socket.gethostname()
    print(f"[REPORT TASK] Worker: {worker} | Generating report {report_id}")
    
    time.sleep(seconds)
    
    print(f"[REPORT TASK DONE] Worker: {worker} | Report {report_id} ready")
    
    return f"Report {report_id} generated"


@shared_task
def send_email_async(subject, recipient_email, template_name=None, context=None, message=''):
    """
    Async task to send emails with HTML support.
    """

    html_message = None
    if template_name and context:
        html_message = render_to_string(template_name, context)
        if not message:
            message = "Please view this email in an HTML-compatible email viewer."

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient_email],
        html_message=html_message,
        fail_silently=False,
    )
    
    return f"Email sent to {recipient_email}"

@shared_task(queue="email_queue")
def send_purchase_confirmation_email(user_email, course_name, amount, transaction_id, invoice_url=None, date=None):
    """
    Task to send purchase confirmation email.
    """
    
    html_message = render_to_string('payments/email/purchase_confirmation.html', {
        'course_name': course_name,
        'amount': amount,
        'transaction_id': transaction_id,
        'invoice_url': invoice_url,
        'date': date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    send_mail(
        subject=f"Purchase Confirmation - {course_name}",
        message=f"Thank you for purchasing {course_name}. Amount: {amount}. Transaction ID: {transaction_id}.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        html_message=html_message,
        fail_silently=False,
    )
    
    
    return f"Purchase confirmation email sent to {user_email}"

@shared_task(queue="email_queue")
def send_invitation_email(user_email, first_name, activation_url):
    """
    Task to send invitation email with activation link.
    """
    
    html_message = render_to_string('accounts/email/invitation_email.html', {
        'first_name': first_name,
        'activation_url': activation_url,
    })
    
    send_mail(
        subject="Invitation to B2B Course Platform",
        message=f"Hello {first_name}, you have been invited to join. Please activate your account: {activation_url}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        html_message=html_message,
        fail_silently=False,
    )
    
    return f"Invitation email sent to {user_email}"

@shared_task(queue="email_queue")
def send_password_reset_email(user_email, context):
    """
    Task to send password reset email.
    """
    html_message = render_to_string('accounts/email/password_reset_email.html', context)
    plaintext_message = render_to_string('accounts/email/password_reset_email.txt', context)

    send_mail(
        subject="Password Reset for {title}".format(title="B2B Course Platform"),
        message=f"Hello {context['username']}, you have requested a password reset. Please reset your password: {context['reset_password_url']}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        html_message=html_message,
        fail_silently=False,
    )

    msg = EmailMultiAlternatives(
        # title:
        "Password Reset for {title}".format(title="B2B Course Platform"),
        # message:
        plaintext_message,
        # from:
        settings.DEFAULT_FROM_EMAIL,
        # to:
        [user_email]
    )
    msg.attach_alternative(html_message, "text/html")
    msg.send()
    
    return f"Password reset email sent to {user_email}"
