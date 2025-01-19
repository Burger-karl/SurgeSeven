from django.views.generic import ListView, TemplateView
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views import View
from django.utils.decorators import method_decorator
from users.models import User
from subscriptions.models import UserSubscription
from booking.models import Booking, Truck
from delivery.models import DeliverySchedule, DeliveryHistory
from payment.models import Payment
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

# Create your views here.

@method_decorator(login_required, name='dispatch')
class ClientHomeView(ListView):
    model = Truck
    template_name = 'dashboard/client_home.html'
    context_object_name = 'available_trucks'

    def get_queryset(self):
        return Truck.objects.filter(available=True).only('image', 'weight_range')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = "Welcome Client!"
        return context


@method_decorator(login_required, name='dispatch')
class TruckOwnerHomeView(ListView):
    model = Truck
    template_name = 'dashboard/truck_owner_home.html'
    context_object_name = 'available_trucks'

    def get_queryset(self):
        return Truck.objects.filter(available=True).only('image', 'weight_range')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = "Welcome Truck Owner!"
        return context


@method_decorator(login_required, name='dispatch')
class AdminHomeView(TemplateView):
    template_name = 'dashboard/admin_home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = "Welcome Admin!"
        return context


@method_decorator(login_required,name='dispatch')
class AboutView(View):
    def get(self, request):
        return render(request, 'dashboard/about.html')
    


class ClientDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/client_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

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
            subscription_data = {
                'plan': subscription.plan.name if subscription.plan else "No Plan",
                'start_date': subscription.start_date,
                'end_date': subscription.end_date,
            }
        except UserSubscription.DoesNotExist:
            subscription_data = None
        
        # Unpaid bookings (payment_completed = False)
        unpaid_bookings = Booking.objects.filter(client=user, payment_completed=False).values(
            'id', 'truck__name', 'product_name', 'product_value', 'pickup_state', 'destination_state', 'delivery_cost'
        )

        # Delivery schedules
        delivery_schedules = DeliverySchedule.objects.filter(client=user).values(
            'booking__truck__name', 'booking__product_name', 'booking__total_delivery_cost', 
            'booking__destination_state', 'status'
        )

        # Delivery histories
        delivery_histories = DeliveryHistory.objects.filter(client=user).values(
            'booking__truck__image', 'booking__product_name', 'booking__destination_state', 
            'booking__insurance_payment', 'booking__total_delivery_cost'
        )

        # Payment history
        payment_history = Payment.objects.filter(user=user).values(
            'amount', 'ref', 'subscription__name', 'booking__product_name', 'date_created'
        ).order_by('-date_created')

        # Context data
        context.update({
            'profile': profile_data,
            'subscription': subscription_data,
            'unpaid_bookings': list(unpaid_bookings),
            'delivery_schedules': list(delivery_schedules),
            'delivery_histories': list(delivery_histories),
            'payment_history': list(payment_history),
        })

        return context



# class TruckOwnerDashboardView(LoginRequiredMixin, TemplateView):
#     template_name = 'dashboard/truck_owner_dashboard.html'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         user = self.request.user

#         # Profile details
#         profile_data = {
#             'profile_image': user.profile.profile_image.url if user.profile.profile_image else None,
#             'full_name': user.profile.full_name,
#             'address': user.profile.address,
#             'phone_number': user.profile.phone_number,
#             'state': user.profile.state,
#         }

#         # Pending trucks
#         pending_trucks = Truck.objects.filter(owner=user, available=False)

#         # Available trucks
#         available_trucks = Truck.objects.filter(owner=user, available=True)

#         # Trucks that have been successfully booked and paid for by a client
#         booked_trucks = Booking.objects.filter(
#             truck__owner=user, 
#             booking_status='active', 
#             payment_completed=True
#         )

#         # Add all context data
#         context.update({
#             'profile': profile_data,
#             'pending_trucks': pending_trucks,
#             'available_trucks': available_trucks,
#             'booked_trucks': booked_trucks,
#         })

#         return context


class TruckOwnerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/truck_owner_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Profile details (already perfect)
        profile_data = {
            'profile_image': user.profile.profile_image.url if user.profile.profile_image else None,
            'full_name': user.profile.full_name,
            'address': user.profile.address,
            'phone_number': user.profile.phone_number,
            'state': user.profile.state,
        }

        # Truck details
        pending_trucks = Truck.objects.filter(owner=user, available=False).values(
            'id', 'name', 'weight_range', 'image'
        )
        available_trucks = Truck.objects.filter(owner=user, available=True).values(
            'id', 'name', 'weight_range', 'image'
        )

        # Bookings for trucks owned by the truck owner
        active_bookings = Booking.objects.filter(
            truck__owner=user, booking_status='active', payment_completed=True
        ).values(
            'id', 'product_name', 'product_value', 'pickup_state', 'destination_state',
            'delivery_cost', 'client__username', 'truck__name', 'truck__weight_range'
        )

        # # Delivery schedules for trucks owned by the truck owner
        # delivery_schedules = DeliverySchedule.objects.filter(
        #     booking__truck__owner=user
        # ).values(
        #     'booking__truck__name', 'booking__product_name', 'status',
        #     'booking__destination_state', 'booking__total_delivery_cost'
        # )

        # Delivery histories for trucks owned by the truck owner
        delivery_histories = DeliveryHistory.objects.filter(
            booking__truck__owner=user
        ).values(
            'booking__truck__name', 'booking__product_name', 'booking__destination_state',
            'booking__insurance_payment', 'booking__total_delivery_cost'
        )

        # Payment history for trucks owned by the truck owner
        payment_history = Payment.objects.filter(
            booking__truck__owner=user
        ).values(
            'amount', 'ref', 'booking__product_name', 'date_created'
        ).order_by('-date_created')

        # Add all context data
        context.update({
            'profile': profile_data,
            'pending_trucks': list(pending_trucks),
            'available_trucks': list(available_trucks),
            'active_bookings': list(active_bookings),
            # 'delivery_schedules': list(delivery_schedules),
            'delivery_histories': list(delivery_histories),
            'payment_history': list(payment_history),
        })

        return context
