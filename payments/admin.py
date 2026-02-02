from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'amount', 'status', 'tenant', 'created_at']
    list_filter = ['tenant', 'status', 'created_at']
    search_fields = ['user__email', 'course__name']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['user', 'course']

    fieldsets = (
        ('Transaction Info', {
            'fields': ('status',)
        }),
        ('User & Course', {
            'fields': ('tenant', 'user', 'course', 'amount')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
        ('Stripe Details', {
            'fields': ('stripe_checkout_session_id', 'stripe_payment_intent_id'),
            'classes': ('collapse',)
        }),
        ('Gateway Data', {
            'fields': ('gateway_response',),
            'classes': ('collapse',)
        }),
    )
