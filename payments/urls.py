from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, StripeWebhookView

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    path('payments/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('', include(router.urls)),
]
