from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from tenants.models import AbstractTenantModel
from courses.models import Course
import uuid


class Payment(AbstractTenantModel):

    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        COMPLETED = 'COMPLETED', _('Completed')
        FAILED = 'FAILED', _('Failed')
        REFUNDED = 'REFUNDED', _('Refunded')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Payment amount in the platform's currency"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    # transaction_id = models.CharField(
    #     max_length=100,
    #     unique=True,
    #     blank=True,
    #     help_text="Unique transaction identifier"
    # )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Additional fields for tracking
    gateway_response = models.JSONField(
        null=True,
        blank=True,
        help_text="Raw response from payment gateway"
    )
    
    # Stripe-specific fields
    stripe_checkout_session_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        help_text="Stripe Checkout Session ID"
    )
    stripe_payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Stripe PaymentIntent ID"
    )
    
 
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.course.name} - {self.amount} ({self.status})"

    # def save(self, *args, **kwargs):
    #     if not self.transaction_id:
    #         self.transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
    #     super().save(*args, **kwargs)
