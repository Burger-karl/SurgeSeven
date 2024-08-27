from .models import DeliverySchedule, DeliveryHistory
from datetime import datetime

def confirm_booking(booking):
    if booking.payment_completed and booking.booking_status == 'active':
        delivery_schedule = DeliverySchedule.objects.create(
            booking=booking,
            scheduled_date=datetime.now().date()  # Automatically set the scheduled date to the current date
        )

        DeliveryHistory.objects.create(
            booking=booking,
            delivery_date=datetime.now().date(),
            status='pending'
        )
