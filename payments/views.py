from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.utils import timezone
from django.db.models import Sum
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse
import json
from tenants.models import Tenant

from .models import Payment
from .serializers import (
    PaymentSerializer,
    StripeCheckoutSerializer,
    StripeCheckoutResponseSerializer,
)
from .stripe_service import StripeService
from accounts.models import User
from accounts.permissions import IsSuperAdmin, IsTenantAdmin, RolePermission
from courses.models import Course
from enrollments.models import Enrollment
from accounts.tasks import send_purchase_confirmation_email


from drf_spectacular.utils import extend_schema

class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing payments.
    - TenantUser: View own payments, create checkout sessions
    - TenantAdmin: View all tenant payments
    - SuperAdmin: View all payments, revenue analytics
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def get_permissions(self):
        if self.action in ['all_tenant_payments','revenue_analytics']:
            return [IsTenantAdmin()]
        return [RolePermission()]

    def get_queryset(self):
        return Payment.objects.for_current_user().select_related('user', 'course', 'tenant')


    @action(detail=False, methods=['get'], url_path='tenant-payments')
    def all_tenant_payments(self, request):
        """
        TenantAdmin: View all payments for their tenant.
        """
        if not request.user.tenant:
            return Response([])
            
        payments = Payment.objects.for_current_user()
        if request.user.role_name == 'SUPER_ADMIN':
            if request.query_params.get('tenant'):
                payments = payments.filter(tenant=request.query_params.get('tenant'))
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=StripeCheckoutSerializer,
        responses={201: StripeCheckoutResponseSerializer}
    )
    @action(detail=False, methods=['post'], url_path='create-checkout')
    def create_checkout(self, request):
        serializer = StripeCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        course_slug = serializer.validated_data['course_slug']

        try:
            course = Course.objects.get(slug=course_slug)
            if course.status == "ARCHIVED":
                return Response(
                    {'error': 'Course is archived'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Course.DoesNotExist:
            return Response(
                {'error': 'Course not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        user = request.user

        # Validate course is paid
        if course.is_free:
            return Response(
                {'error': 'This course is free. Use enrollment endpoint instead.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if already enrolled
        if Enrollment.objects.filter(user=user, course=course).exists():
            return Response(
                {'error': 'You are already enrolled in this course.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for existing pending payment
        existing_payment = Payment.objects.filter(
            user=user,
            course=course,
            status=Payment.Status.PENDING
        ).first()

        if existing_payment and existing_payment.stripe_checkout_session_id:
            # Try to retrieve existing session
            try:
                session = StripeService.retrieve_session(
                    existing_payment.stripe_checkout_session_id
                )
                if session.status == 'open':
                    return Response({
                        'checkout_url': session.url,
                        'session_id': session.id,
                        'payment_id': existing_payment.id,
                        'message': 'Existing checkout session found'
                    })
            except Exception:
                pass  # Session expired, create new one

        # Create new payment record
        payment = Payment.objects.create(
            tenant=user.tenant,
            user=user,
            course=course,
            amount=course.price,
            status=Payment.Status.PENDING
        )

        # Create Stripe Checkout Session
        try:
            checkout_data = StripeService.create_checkout_session(
                user=user,
                course=course,
                payment_record=payment
            )

            # Update payment with Stripe session ID
            payment.stripe_checkout_session_id = checkout_data['session_id']
            payment.save()

            return Response({
                'checkout_url': checkout_data['checkout_url'],
                'session_id': checkout_data['session_id'],
                'payment_id': payment.id,
                'expires_at': checkout_data.get('expires_at')
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            payment.status = Payment.Status.FAILED
            payment.save()
            return Response(
                {'error': f'Failed to create checkout session: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='verify-session/(?P<session_id>[^/.]+)')
    def verify_session(self, request, session_id=None):
        """
        Verify a Stripe Checkout Session status.
        Called by frontend after redirect from Stripe.
        """
        try:
            session = StripeService.retrieve_session(session_id)
            payment = Payment.objects.filter(
                stripe_checkout_session_id=session_id
            ).first()

            return Response({
                'status': session.status,
                'payment_status': session.payment_status,
                'payment_id': payment.id if payment else None,
                'payment_local_status': payment.status if payment else None,
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], url_path='revenue-analytics')
    def revenue_analytics(self, request):
        """
        SuperAdmin: Get platform-wide revenue analytics.
        tenant admin: Get tenant-wise revenue analytics.
        """

        analytics = []
        if request.user.role_name == 'SUPER_ADMIN':
            tenants = Tenant.objects.filter(is_active=True)
        else:
            tenant = Tenant.objects.get(id=request.user.tenant.id)
            tenant_payments = Payment.objects.filter(tenant=tenant)
            completed = tenant_payments.filter(status=Payment.Status.COMPLETED)
            return Response({
                'tenant_name': tenant.name,
                'user_count': tenant.users.count(),
                'course_count': tenant.course_set.count(),
                'enrollment_count': tenant.enrollment_set.count(),
                'total_revenue': completed.aggregate(Sum('amount'))['amount__sum'] or 0,
                'total_transactions': tenant_payments.count(),
                'completed_payments': completed.count(),
                'total_amount': tenant_payments.aggregate(Sum('amount'))['amount__sum'] or 0,
                'pending_payments': tenant_payments.filter(status=Payment.Status.PENDING).count(),
                'failed_payments': tenant_payments.filter(status=Payment.Status.FAILED).count(),
            })

        for tenant in tenants:
            tenant_payments = Payment.objects.filter(tenant=tenant)
            completed = tenant_payments.filter(status=Payment.Status.COMPLETED)

            analytics.append({
                'tenant_name': tenant.name,
                'user_count': tenant.users.count(),
                'course_count': tenant.course_set.count(),
                'enrollment_count': tenant.enrollment_set.count(),
                'total_revenue': completed.aggregate(Sum('amount'))['amount__sum'] or 0,
                'total_transactions': tenant_payments.count(),
                'completed_payments': completed.count(),
                'total_amount': tenant_payments.aggregate(Sum('amount'))['amount__sum'] or 0,
                'pending_payments': tenant_payments.filter(status=Payment.Status.PENDING).count(),
                'failed_payments': tenant_payments.filter(status=Payment.Status.FAILED).count(),
            })

        # Platform totals

        all_completed = Payment.objects.filter(status=Payment.Status.COMPLETED)
        platform_total = {
            'tenant_name': 'PLATFORM_TOTAL',
            'user_count': User.objects.exclude(role__name__in=['SUPER_ADMIN', 'TENANT_ADMIN']).count(),
            'course_count': Course.objects.count(),
            'enrollment_count': Enrollment.objects.count(),
            'total_revenue': all_completed.aggregate(Sum('amount'))['amount__sum'] or 0,
            'total_transactions': Payment.objects.count(),
            'completed_payments': all_completed.count(),
            'total_amount': all_completed.aggregate(Sum('amount'))['amount__sum'] or 0,
            'pending_payments': Payment.objects.filter(status=Payment.Status.PENDING).count(),
            'failed_payments': Payment.objects.filter(status=Payment.Status.FAILED).count(),
        }

        return Response({
            'tenants': analytics,
            'platform_total': platform_total
        })

    @action(detail=False, methods=['get'], url_path='my-payments')
    def my_payments(self, request):
        """
        Get current user's payment history.
        """
        payments = Payment.objects.filter(user=request.user)
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)


@extend_schema(exclude=True)
@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """
    Handle Stripe webhook events.
    This endpoint is called by Stripe when payment events occur.
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

        try:
            event = StripeService.verify_webhook_signature(payload, sig_header)
        except ValueError as e:
            return HttpResponse(str(e), status=400)

        # Handle the event
        if event['type'] == 'checkout.session.completed':
            self.handle_checkout_completed(event['data']['object'])
        elif event['type'] == 'checkout.session.expired':
            self.handle_checkout_expired(event['data']['object'])
        elif event['type'] == 'payment_intent.payment_failed':
            self.handle_payment_failed(event['data']['object'])

        return HttpResponse(status=200)

    def handle_checkout_completed(self, session):
        """
        Handle successful checkout session completion.
        Creates enrollment for the user.
        """
        session_id = session['id']
        payment_intent_id = session.get('payment_intent')

        # Find the payment record
        try:
            payment = Payment.objects.get(stripe_checkout_session_id=session_id)
        except Payment.DoesNotExist:
            return  # Payment not found, possibly created elsewhere

        # Update payment status
        payment.status = Payment.Status.COMPLETED
        payment.stripe_payment_intent_id = payment_intent_id
        payment.completed_at = timezone.now()
        payment.gateway_response = dict(session)
        payment.save()

        # Create enrollment

        Enrollment.objects.get_or_create(
            tenant=payment.tenant,
            user=payment.user,
            course=payment.course,
            defaults={'status': 'NOT_STARTED'}
        )

        # Send confirmation email
        invoice_id = session.get('invoice')
        invoice_url = None
        
        if invoice_id:
            invoice_url = StripeService.get_invoice_pdf_url(invoice_id)
            
        if not invoice_url:
             invoice_url = StripeService.get_receipt_url(payment_intent_id)

        send_purchase_confirmation_email.delay(
            user_email=payment.user.email,
            course_name=payment.course.name,
            amount=str(payment.amount),
            transaction_id=payment.stripe_payment_intent_id,
            invoice_url=invoice_url
        )

    def handle_checkout_expired(self, session):
        """
        Handle expired checkout session.
        """
        session_id = session['id']

        try:
            payment = Payment.objects.get(stripe_checkout_session_id=session_id)
            if payment.status == Payment.Status.PENDING:
                payment.status = Payment.Status.FAILED
                payment.save()
        except Payment.DoesNotExist:
            pass

    def handle_payment_failed(self, payment_intent):
        """
        Handle failed payment.
        """
        payment_intent_id = payment_intent['id']

        try:
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
            payment.status = Payment.Status.FAILED
            payment.gateway_response = dict(payment_intent)
            payment.save()
        except Payment.DoesNotExist:
            pass
