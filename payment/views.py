from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from .paystack_client import PaystackClient
from .models import Payment
from subscriptions.models import SubscriptionPlan, UserSubscription
from django.contrib.auth.decorators import login_required
import uuid
from django.contrib import messages
from booking.models import Booking

# Create your views here.

paystack_client = PaystackClient()

@login_required
def create_subscription_payment(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    user = request.user
    amount = int(plan.price * 100)  # Paystack expects amount in kobo (1 Naira = 100 kobo)
    email = user.email
    subscription_code = str(uuid.uuid4())  # Generate a unique subscription code

    # Create a UserSubscription with an initial status
    user_subscription = UserSubscription.objects.create(
        user=user,
        plan=plan,
        start_date=timezone.now(),
        end_date=timezone.now() + plan.duration,
        is_active=False,
        payment_completed=False,
        subscription_status='pending',
        subscription_code=subscription_code
    )

    # Build the callback URL using the generated subscription code
    callback_url = request.build_absolute_uri(reverse('verify-payment', kwargs={'ref': subscription_code}))

    # Initialize Paystack transaction
    response = paystack_client.initialize_transaction(email, amount, subscription_code, callback_url)

    if response['status']:
        return redirect(response['data']['authorization_url'])
    else:
        return render(request, 'subscriptions/subscribe.html', {'plan': plan, 'error': 'Payment initialization failed.'})



@login_required
def verify_payment(request, ref):
    # Verify the payment with Paystack using the reference
    response = paystack_client.verify_transaction(ref)

    if response['status'] and response['data']['status'] == 'success':
        # Update the subscription status or perform other actions
        user_subscription = UserSubscription.objects.get(subscription_code=ref)
        user_subscription.payment_completed = True
        user_subscription.is_active = True
        user_subscription.subscription_status = 'active'
        user_subscription.save()
        return redirect('user-subscriptions')
    else:
        return render(request, 'subscriptions/subscribe.html', {'error': 'Payment verification failed.'})



@login_required
def create_booking_payment_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    user = request.user

    if booking.payment_completed:
        messages.error(request, 'Payment already completed for this booking.')
        return redirect('booking_list', booking_id=booking_id)

    amount = int(booking.delivery_cost * 100)  # Paystack expects amount in kobo
    email = user.email
    booking_code = str(uuid.uuid4())

    booking.payment_completed = False
    booking.booking_code = booking_code
    booking.save()

    callback_url = request.build_absolute_uri(reverse('verify_booking_payment', kwargs={'ref': booking_code}))

    response = paystack_client.initialize_transaction(email, amount, booking_code, callback_url)

    if response['status']:
        return redirect(response['data']['authorization_url'])
    else:
        booking.booking_code = None
        booking.save()
        messages.error(request, 'Payment initialization failed.')
        return redirect('booking_list', booking_id=booking_id)


import logging

logger = logging.getLogger(__name__)

@login_required
def verify_booking_payment_view(request, ref):
    response = paystack_client.verify_transaction(ref)

    logger.debug('Paystack verification response: %s', response)

    if response['status'] and response['data']['status'] == 'success':
        booking = get_object_or_404(Booking, booking_code=ref)
        booking.payment_completed = True
        booking.booking_status = 'active'
        booking.save()

        Payment.objects.create(
            user=request.user,
            booking=booking,
            amount=booking.delivery_cost,
            ref=ref,
            email=request.user.email,
            verified=True
        )

        messages.success(request, 'Payment successful')
        return redirect('booking_list', booking_id=booking.id)
    else:
        messages.error(request, 'Payment verification failed.')
        return redirect('booking_list', booking_id=booking.id)
