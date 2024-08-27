from django.db import models
from booking.models import Booking

# Create your models here.

class DeliverySchedule(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered')
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    scheduled_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Delivery Schedule for Booking {self.booking.id} - {self.status}"

class DeliveryHistory(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    delivery_date = models.DateField()
    status = models.CharField(max_length=10, choices=DeliverySchedule.STATUS_CHOICES)

    def __str__(self):
        return f"Delivery History for Booking {self.booking.id} - {self.status}"


class DeliveryDocument(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    document = models.FileField(upload_to='delivery_documents/')

    def __str__(self):
        return f"Delivery Document for Booking {self.booking.id}"
