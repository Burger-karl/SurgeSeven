from django.db import models
from datetime import timedelta
from users.models import User  

# Create your models here.

class SubscriptionPlan(models.Model):
    FREE = 'free'
    BASIC = 'basic'
    PREMIUM = 'premium'
    PLAN_CHOICES = [
        (FREE, 'Free'),
        (BASIC, 'Basic'),
        (PREMIUM, 'Premium'),
    ]

    name = models.CharField(max_length=10, choices=PLAN_CHOICES, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    duration = models.DurationField(default=timedelta(days=0))  # Free plan has no duration
    plan_code = models.CharField(max_length=100, default='default_plan_code')
    features = models.JSONField(default=dict)  # Store features as a JSON field

    def __str__(self):
        return self.name

    @classmethod
    def create_default_plans(cls):
        cls.objects.get_or_create(
            name=cls.FREE,
            defaults={
                'price': 0.00,
                'duration': timedelta(days=0),  # Unlimited duration
                'features': {}
            }
        )
        cls.objects.get_or_create(
            name=cls.BASIC,
            defaults={
                'price': 3000.00,
                'duration': timedelta(days=180),  # 6 months
                'features': {
                    'Booking app': True,
                    'Tracking System': True
                }
            }
        )
        cls.objects.get_or_create(
            name=cls.PREMIUM,
            defaults={
                'price': 5000.00,
                'duration': timedelta(days=180),  # 6 months
                'features': {
                    'Booking app': True,
                    'Tracking System': True,
                    'Insurance Coverage': True
                }
            }
        )

class UserSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    payment_completed = models.BooleanField(default=False)
    subscription_status = models.CharField(max_length=10, default='inactive')
    subscription_code = models.CharField(max_length=100, null=True, blank=True)  # Subscription code for Paystack

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"

    def activate_subscription(self):
        self.is_active = True
        self.subscription_status = 'active'
        self.end_date = self.start_date + self.plan.duration
        self.save()

    def deactivate_subscription(self):
        self.is_active = False
        self.subscription_status = 'inactive'
        self.save()

    
    def renew_subscription(self):
        """
        Renews the current subscription by extending the end date.
        Ensures the subscription is active and the payment is marked as completed.
        """
        if not self.is_active:
            raise ValueError("Cannot renew an inactive subscription. Please activate the subscription first.")

        if not self.payment_completed:
            raise ValueError("Payment not completed. Cannot renew subscription.")

        # Extend the subscription end date by the duration of the plan
        self.end_date += self.plan.duration
        self.save()

        return self.end_date

