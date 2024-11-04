from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from booking.models import Booking
from datetime import datetime
from .models import DeliverySchedule, DeliveryHistory

@receiver(post_save, sender=Booking)
def create_delivery_schedule(sender, instance, created, **kwargs):
    # Check if this is an update and payment has been completed
    if not created and instance.payment_completed:
        # Check if a delivery schedule already exists for this booking
        delivery_schedule, created = DeliverySchedule.objects.get_or_create(
            booking=instance,
            client=instance.client,
            defaults={
                'scheduled_date': timezone.now().date(),
                'status': 'pending'
            }
        )
        if not created:
            print(f"Delivery Schedule already exists for Booking {instance.id}")



# @receiver(post_save, sender=Booking)
# def create_delivery_schedule_and_history(sender, instance, created, **kwargs):

#     if created and instance.booking_status == 'active' and instance.payment_completed:
#         scheduled_date = datetime.now().date()
#         DeliverySchedule.objects.create(
#             booking=instance,
#             scheduled_date=scheduled_date
#         )
#         DeliveryHistory.objects.create(
#             booking=instance,
#             delivery_date=scheduled_date,
#             status='pending'
#         )