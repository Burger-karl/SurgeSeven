from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView, View
from django.urls import reverse_lazy
from .forms import TruckForm, BookingForm
from .models import Truck, Booking
from subscriptions.models import UserSubscription

# Decorator to check if user is logged in and has the required user type
def user_type_required(user_type):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated or request.user.user_type != user_type:
                raise PermissionDenied(f"Only {user_type}s can access this view.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# Truck Create View
@method_decorator([login_required, user_type_required('truck_owner')], name='dispatch')
class TruckCreateView(CreateView):
    model = Truck
    form_class = TruckForm
    template_name = 'booking/truck_form.html'
    success_url = reverse_lazy('truck_list')

    def form_valid(self, form):
        truck = form.save(commit=False)
        truck.owner = self.request.user
        truck.save()
        return super().form_valid(form)

# Truck List View
@method_decorator(login_required, name='dispatch')
class TruckListView(ListView):
    model = Truck
    template_name = 'booking/truck_list.html'
    context_object_name = 'trucks'

    def get_queryset(self):
        if self.request.user.user_type == 'truck_owner':
            return Truck.objects.filter(owner=self.request.user)
        return Truck.objects.filter(available=True)

# Booking Create View
@method_decorator([login_required, user_type_required('client')], name='dispatch')
class BookingCreateView(CreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'booking/booking_form.html'
    success_url = reverse_lazy('booking-list')

    def form_valid(self, form):
        active_subscription = UserSubscription.objects.filter(
            user=self.request.user,
            subscription_status='active',
            is_active=True
        ).exclude(plan__name='free').exists()

        if not active_subscription:
            raise PermissionDenied("You must have an active paid subscription to book a truck.")

        booking = form.save(commit=False)
        booking.client = self.request.user
        booking.save()
        return super().form_valid(form)

# Booking List View
@method_decorator(login_required, name='dispatch')
class BookingListView(ListView):
    model = Booking
    template_name = 'booking/booking_list.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        if self.request.user.user_type == 'client':
            return Booking.objects.filter(client=self.request.user)
        elif self.request.user.user_type == 'truck_owner':
            return Booking.objects.filter(truck__owner=self.request.user)
        return Booking.objects.none()

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import ListView, View
from django.urls import reverse_lazy
from django.contrib import messages

from .models import Truck
from .forms import TruckApprovalForm

# Decorator to ensure user is superuser/admin
def admin_required(view_func):
    decorated_view_func = login_required(user_passes_test(lambda u: u.is_superuser)(view_func))
    return decorated_view_func

@method_decorator(admin_required, name='dispatch')
class AdminTruckListView(View):
    template_name = 'booking/admin_truck_list.html'
    success_url = reverse_lazy('admin_truck_list')

    def get(self, request):
        trucks = Truck.objects.filter(available=False)
        form = TruckApprovalForm()
        context = {
            'trucks': trucks,
            'form': form,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form = TruckApprovalForm(request.POST)
        if form.is_valid():
            truck_ids = form.cleaned_data.get('truck_ids')
            if truck_ids:
                updated_count = Truck.objects.filter(id__in=truck_ids).update(available=True)
                messages.success(request, f'{updated_count} truck(s) have been approved successfully.')
            else:
                messages.warning(request, 'No trucks were selected for approval.')
        else:
            messages.error(request, 'Invalid form submission.')
        return redirect(self.success_url)

@method_decorator(admin_required, name='dispatch')
class AdminTruckDetailView(View):
    template_name = 'booking/admin_truck_detail.html'
    success_url = reverse_lazy('admin_truck_list')

    def get(self, request, pk):
        truck = get_object_or_404(Truck, pk=pk)
        context = {
            'truck': truck
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        truck = get_object_or_404(Truck, pk=pk)
        action = request.POST.get('action')
        if action == 'approve':
            truck.available = True
            truck.save()
            messages.success(request, f'Truck "{truck.name}" has been approved.')
        elif action == 'reject':
            truck.delete()
            messages.success(request, f'Truck "{truck.name}" has been rejected and removed.')
        else:
            messages.error(request, 'Invalid action.')
        return redirect(self.success_url)

# Admin - Booking Update Delivery Cost View
@method_decorator([login_required, user_passes_test(lambda u: u.is_superuser)], name='dispatch')
class BookingUpdateDeliveryCostView(View):
    def get(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        return render(request, 'booking/update_delivery_cost.html', {'booking': booking})

    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        delivery_cost = request.POST.get("delivery_cost")
        if not delivery_cost:
            raise PermissionDenied("Delivery cost is required.")
        booking.delivery_cost = delivery_cost
        booking.save()
        return redirect('booking-list')
