"""
Stripe service layer for handling payment operations.
Centralizes Stripe API interactions.
"""
import stripe
from django.conf import settings
from typing import Optional, Dict, Any

# Initialize Stripe with secret key
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """
    Service class for Stripe payment operations.
    """

    @staticmethod
    def create_checkout_session(
        user,
        course,
        payment_record,

    ) -> Dict[str, Any]:
        success_url = settings.STRIPE_SUCCESS_URL
        cancel_url = settings.STRIPE_CANCEL_URL

        amount_cents = int(course.price * 100)

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',  
                        'product_data': {
                            'name': course.name,
                            'description': course.description[:500] if course.description else f'Access to {course.name}',
                            'metadata': {
                                'course_id': str(course.id),
                                'course_slug': course.slug,
                            }
                        },
                        'unit_amount': amount_cents,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=user.email,
                metadata={
                    'payment_id': str(payment_record.id),
                    'user_id': str(user.id),
                    'user_email': user.email,
                    'course_id': str(course.id),
                    'course_slug': course.slug,
                    'tenant_id': str(user.tenant.id) if user.tenant else '',
                },
                invoice_creation={"enabled": True},
                expires_at=None,  # Default 24hr expiration
            )

            return {
                'session_id': session.id,
                'checkout_url': session.url,
                'expires_at': session.expires_at,
            }

        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")

    @staticmethod
    def retrieve_session(session_id: str) -> stripe.checkout.Session:
        """
        Retrieve a Checkout Session by ID.
        """
        try:
            return stripe.checkout.Session.retrieve(session_id)
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to retrieve session: {str(e)}")

    @staticmethod
    def verify_webhook_signature(payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Verify and construct webhook event from Stripe.
        
        Args:
            payload: Raw request body
            signature: Stripe-Signature header value
            
        Returns:
            Constructed Stripe event object
        """
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except stripe.error.SignatureVerificationError as e:
            raise ValueError(f"Invalid signature: {str(e)}")
        except Exception as e:
            raise ValueError(f"Webhook error: {str(e)}")

    @staticmethod
    def retrieve_payment_intent(payment_intent_id: str) -> stripe.PaymentIntent:
        """
        Retrieve a PaymentIntent by ID.
        """
        try:
            return stripe.PaymentIntent.retrieve(payment_intent_id)
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to retrieve payment intent: {str(e)}")

    @staticmethod
    def create_refund(payment_intent_id: str, amount: Optional[int] = None) -> stripe.Refund:
        """
        Create a refund for a PaymentIntent.
        
        Args:
            payment_intent_id: The PaymentIntent ID to refund
            amount: Amount in cents to refund (None for full refund)
        """
        try:
            refund_params = {'payment_intent': payment_intent_id}
            if amount:
                refund_params['amount'] = amount
            return stripe.Refund.create(**refund_params)
        except stripe.error.StripeError as e:
            raise Exception(f"Refund failed: {str(e)}")

    @staticmethod
    def get_receipt_url(payment_intent_id: str) -> Optional[str]:
        """
        Retrieve the receipt URL from a PaymentIntent.
        """
        try:
            payment_intent = StripeService.retrieve_payment_intent(payment_intent_id)
            if payment_intent.latest_charge:
                 # Check if latest_charge is an ID (string) or object.
                 # Expand likely required if it's an ID, but let's try retrieving the charge.
                 charge_id = payment_intent.latest_charge
                 if isinstance(charge_id, str):
                     charge = stripe.Charge.retrieve(charge_id)
                     return charge.receipt_url
                 else:
                     # It's already an object
                     return charge_id.receipt_url
            return None
        except Exception:
            return None

    @staticmethod
    def get_invoice_pdf_url(invoice_id: str) -> Optional[str]:
        """
        Retrieve the hosted invoice PDF URL from an invoice ID.
        """
        try:
            invoice = stripe.Invoice.retrieve(invoice_id)
            return invoice.invoice_pdf
        except Exception:
            return None
