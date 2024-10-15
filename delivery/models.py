from django.db import models
from django.contrib.auth import get_user_model  # Use this to get the custom user model if it exists
from booking.models import Booking

# Get the user model
User = get_user_model()

class DeliverySchedule(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered')
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_schedules')  # New field
    scheduled_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Delivery Schedule for Booking {self.booking.id} - {self.status}"

class DeliveryHistory(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_histories')  # New field
    delivery_date = models.DateField()
    status = models.CharField(max_length=10, choices=DeliverySchedule.STATUS_CHOICES)

    def __str__(self):
        return f"Delivery History for Booking {self.booking.id} - {self.status}"
