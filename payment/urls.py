from django.urls import path
from . import views


urlpatterns = [
    path('subscription/<int:plan_id>/', views.create_subscription_payment, name='create-subscription-payment'),
    path('verify-payment/<str:ref>/', views.verify_payment, name='verify-payment'),
    path('bookings/<int:booking_id>/payment/', views.create_booking_payment_view, name='create_booking_payment'),
    path('verify-booking-payment/<str:ref>/', views.verify_booking_payment_view, name='verify_booking_payment'),
]
