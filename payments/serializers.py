from rest_framework import serializers
from .models import Payment
from courses.models import Course


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for Payment model.
    """
    course_name = serializers.CharField(source='course.name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id',
            # 'transaction_id',
            'user_email',
            'course_name',
            'tenant_name',
            'amount',
            'status',
            'stripe_checkout_session_id',
            'stripe_payment_intent_id',
            'created_at',
            'completed_at',
        ]
        read_only_fields = fields


class StripeCheckoutSerializer(serializers.Serializer):
    """
    Serializer for creating a Stripe Checkout Session.
    """
    course_slug = serializers.SlugField(
        help_text="Slug of the course to purchase"
    )

    def validate_course_slug(self, value):
        """Validate that the course exists and is a paid course."""
        try:
            course = Course.objects.get(slug=value)
        except Course.DoesNotExist:
            raise serializers.ValidationError("Course not found")

        if course.is_free:
            raise serializers.ValidationError(
                "This course is free. Use enrollment endpoint instead."
            )

        if course.status != 'PUBLISHED':
            raise serializers.ValidationError(
                "This course is not available for purchase."
            )

        return value


class StripeCheckoutResponseSerializer(serializers.Serializer):
    """
    Response serializer for checkout session creation.
    """
    checkout_url = serializers.URLField()
    session_id = serializers.CharField()
    payment_id = serializers.IntegerField()
    expires_at = serializers.IntegerField(required=False)
