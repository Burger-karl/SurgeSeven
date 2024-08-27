from django.urls import path
from .views import (
    TruckCreateView, TruckListView, BookingCreateView, BookingListView,
    AdminTruckListView, AdminTruckDetailView
)

urlpatterns = [
    path('trucks/create/', TruckCreateView.as_view(), name='truck_create'),
    path('trucks/', TruckListView.as_view(), name='truck_list'),
    path('bookings/create/', BookingCreateView.as_view(), name='booking_create'),
    path('bookings/', BookingListView.as_view(), name='booking_list'),

    # Admin routes
    path('admin/trucks/', AdminTruckListView.as_view(), name='admin_truck_list'),
    path('admin/trucks/<int:pk>/', AdminTruckDetailView.as_view(), name='admin_truck_detail'),
]
