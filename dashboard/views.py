from django.views.generic import ListView
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views import View
from django.utils.decorators import method_decorator
from users.models import User
from subscriptions.models import UserSubscription
from booking.models import Booking, Truck
from delivery.models import DeliverySchedule, DeliveryHistory

# Create your views here.


@method_decorator(login_required, name='dispatch')
class HomeView(ListView):
    model = Truck
    template_name = 'dashboard/home.html'
    context_object_name = 'available_trucks'

    def get_queryset(self):
        return Truck.objects.filter(available=True).only('image', 'weight_range')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


@method_decorator(login_required,name='dispatch')
class AboutView(View):
    def get(self, request):
        return render(request, 'dashboard/about.html')

@login_required
def client_dashboard_view(request):
    user = request.user

    # Profile details
    profile_data = {
        'profile_image': user.profile.profile_image.url if user.profile.profile_image else None,
        'full_name': user.profile.full_name,
        'address': user.profile.address,
        'phone_number': user.profile.phone_number,
        'state': user.profile.state,
    }

    # Current subscription details
    try:
        subscription = UserSubscription.objects.get(user=user, subscription_status='active')
        subscription_data = subscription
    except UserSubscription.DoesNotExist:
        subscription_data = None

    # Unpaid bookings
    unpaid_bookings = Booking.objects.filter(client=user, booking_status='inactive')

    # Delivery schedules
    delivery_schedules = DeliverySchedule.objects.filter(booking__client=user)

    # Delivery histories
    delivery_histories = DeliveryHistory.objects.filter(booking__client=user)

    context = {
        'profile': profile_data,
        'subscription': subscription_data,
        'unpaid_bookings': unpaid_bookings,
        'delivery_schedules': delivery_schedules,
        'delivery_histories': delivery_histories,
    }

    return render(request, 'dashboard/client_dashboard.html', context)


@login_required
def truck_owner_dashboard_view(request):
    user = request.user

    # Profile details
    profile_data = {
        'profile_image': user.profile.profile_image.url if user.profile.profile_image else None,
        'full_name': user.profile.full_name,
        'address': user.profile.address,
        'phone_number': user.profile.phone_number,
        'state': user.profile.state,
    }

    # Pending trucks
    pending_trucks = Truck.objects.filter(owner=user, available=False)

    # Available trucks
    available_trucks = Truck.objects.filter(owner=user, available=True)

    # Trucks that have been successfully booked and paid for by a client
    booked_trucks = Booking.objects.filter(truck__owner=user, booking_status='active', payment_completed=True)

    context = {
        'profile': profile_data,
        'pending_trucks': pending_trucks,
        'available_trucks': available_trucks,
        'booked_trucks': booked_trucks,
    }

    return render(request, 'dashboard/truck_owner_dashboard.html', context)
