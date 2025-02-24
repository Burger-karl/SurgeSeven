from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView, View, DetailView
from django.urls import reverse_lazy
from .forms import TruckForm, BookingForm
from .models import Truck, Booking
from subscriptions.models import UserSubscription, SubscriptionPlan

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
    success_url = reverse_lazy('booking_list')

    def get_initial(self):
        initial = super().get_initial()
        truck_id = self.kwargs.get('truck_id')
        if truck_id:
            initial['truck'] = get_object_or_404(Truck, id=truck_id)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        truck_id = self.kwargs.get('truck_id')
        if truck_id:
            truck = get_object_or_404(Truck, id=truck_id)
            context['truck'] = truck
        return context

    def form_valid(self, form):
        user = self.request.user
        
        # Ensure only clients can make a booking
        if user.user_type != 'client':
            raise PermissionDenied("Only clients can book trucks.")

        # Retrieve the active subscription for the user, excluding the 'free' plan
        active_subscription = UserSubscription.objects.filter(
            user=user,
            subscription_status='active',
            is_active=True
        ).exclude(plan__name=SubscriptionPlan.FREE).first()

        if not active_subscription:
            raise PermissionDenied("You must have an active paid subscription to book a truck.")

        # Determine the insurance payment based on the subscription plan
        if active_subscription.plan.name == SubscriptionPlan.PREMIUM:
            insurance_payment = 150000  # Insurance payment for premium clients
        else:
            insurance_payment = 0  # No insurance payment for basic clients

        # Save the booking with the calculated insurance payment
        booking = form.save(commit=False)
        booking.client = user
        booking.truck = get_object_or_404(Truck, id=self.kwargs.get('truck_id'))
        booking.insurance_payment = insurance_payment

        # Calculate the total delivery cost for premium clients
        if active_subscription.plan.name == SubscriptionPlan.PREMIUM:
            booking.total_delivery_cost = booking.delivery_cost + insurance_payment
        else:
            booking.total_delivery_cost = booking.delivery_cost  # For basic clients, total delivery cost is the same as delivery cost

        booking.save()

        return redirect('booking_list')


# Booking List View
@method_decorator(login_required, name='dispatch')
class BookingListView(ListView):
    model = Booking
    template_name = 'booking/booking_list.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        queryset = Booking.objects.none()  # Initialize an empty queryset

        if self.request.user.user_type == 'client':
            queryset = Booking.objects.filter(client=self.request.user, payment_completed=False)
        elif self.request.user.user_type == 'truck_owner':
            queryset = Booking.objects.filter(truck__owner=self.request.user, payment_completed=False)
        
        return queryset


# Generate Receipt View
@method_decorator(login_required, name='dispatch')
class GenerateReceiptView(DetailView):
    model = Booking
    template_name = 'booking/receipt.html'
    context_object_name = 'booking'

    def get_object(self, queryset=None):
        booking_code = self.kwargs.get('booking_code')
        booking = get_object_or_404(Booking, booking_code=booking_code)
        
        # Ensure only the client who made the booking can view the receipt
        if booking.client != self.request.user:
            raise PermissionDenied("You do not have permission to view this receipt.")
        
        return booking

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking = self.get_object()
        
        # Add truck name to the context
        context['truck_name'] = booking.truck.name
        
        return context
    
    


@method_decorator(login_required, name='dispatch')
class AvailableTruckListView(ListView):
    model = Truck
    template_name = 'booking/booking.html'
    context_object_name = 'available_trucks'

    def get_queryset(self):
        return Truck.objects.filter(available=True).only('image', 'weight_range')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context








from django.db.models import QuerySet
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.urls import reverse_lazy
from django.contrib import messages
from decimal import Decimal
from django.core.exceptions import PermissionDenied
from .models import Truck, Booking
from .forms import TruckApprovalForm

# Decorator to ensure user is superuser/admin
def admin_required(view_func):
    decorated_view_func = login_required(user_passes_test(lambda u: u.is_superuser)(view_func))
    return decorated_view_func

# Admin Truck List View with Pagination
@method_decorator(admin_required, name='dispatch')
class AdminTruckListView(View):
    template_name = 'booking/admin_truck_list.html'
    success_url = reverse_lazy('admin_truck_list')

    def get(self, request):
        trucks = Truck.objects.filter(available=False)
        paginator = Paginator(trucks, 5)  # Show 5 trucks per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        form = TruckApprovalForm()
        context = {
            'page_obj': page_obj,
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


@method_decorator(user_passes_test(admin_required), name='dispatch')
class BookingUpdateDeliveryCostView(View):
    template_name = 'booking/booking_list_admin.html'

    def get(self, request):
        """
        Fetch bookings with no delivery cost assigned and display them in a paginated format.
        """
        bookings = Booking.objects.filter(
            delivery_cost=0.00,  # Delivery cost is not set
            payment_completed=True,  # Payment is completed
            booking_status='pending'  # Pending bookings only
        ).select_related('truck', 'client', 'truck__owner')

        # Paginate bookings
        paginator = Paginator(bookings, 5)  # Show 5 bookings per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, self.template_name, {'bookings': page_obj})

    def post(self, request, pk):
        """
        Update the delivery cost for a specific booking.
        """
        booking = get_object_or_404(Booking, pk=pk)
        delivery_cost = request.POST.get("delivery_cost")

        try:
            # Validate delivery cost input
            delivery_cost = Decimal(delivery_cost)
            if delivery_cost <= 0:
                raise ValueError("Invalid delivery cost.")
        except (ValueError, TypeError):
            messages.error(request, "Please enter a valid positive delivery cost.")
            return redirect('admin-update-delivery-cost')

        # Update booking with delivery cost and calculate total
        booking.delivery_cost = delivery_cost
        booking.total_delivery_cost = delivery_cost + booking.insurance_payment
        booking.booking_status = 'active'  # Activate booking after assigning cost
        booking.save()

        messages.success(request, f"Delivery cost for Booking {booking.pk} updated successfully.")
        return redirect('admin-update-delivery-cost')



# View for Bookings with Updated Delivery Costs with Pagination
@method_decorator(admin_required, name='dispatch')
class BookingWithUpdatedCostView(View):
    template_name = 'booking/updated_cost_booking_list.html'
    
    def get(self, request):
        # Fetch bookings where delivery cost is set
        bookings = Booking.objects.filter(delivery_cost__isnull=False).select_related('truck', 'client', 'truck__owner')
        
        # Add pagination
        paginator = Paginator(bookings, 5)  # Show 5 bookings per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, self.template_name, {'page_obj': page_obj})






from django.shortcuts import render, redirect
from django.views import View
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from booking.models import Booking
from subscriptions.models import UserSubscription, SubscriptionPlan
from django.db.models import F
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


@method_decorator(admin_required, name='dispatch')
class BookingAdminListView(View):

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can view all bookings.")

        queryset = Booking.objects.all()
        bookings_data = []

        for booking in queryset:
            # Get client subscription details
            client_subscription = UserSubscription.objects.filter(
                user=booking.client, subscription_status='active', is_active=True
            ).first()
            client_subscription_name = client_subscription.plan.name if client_subscription else "No active subscription"

            # Prepare booking data with client subscription details
            booking_data = {
                "booking_details": booking,
                "client_details": {
                    "username": booking.client.username,
                    "email": booking.client.email,
                    "current_subscription_plan": client_subscription_name,
                },
            }
            bookings_data.append(booking_data)

        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(bookings_data, 5)  # Show 10 bookings per page

        try:
            bookings_data = paginator.page(page)
        except PageNotAnInteger:
            bookings_data = paginator.page(1)
        except EmptyPage:
            bookings_data = paginator.page(paginator.num_pages)

        # Render the data into a template
        return render(request, "booking/admin_booking_list.html", {
            "bookings_data": bookings_data
        })


        # # Render the data into a template
        # return render(request, "booking/admin_booking_list.html", {"bookings_data": bookings_data})

    def post(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return JsonResponse({"detail": "Permission denied."}, status=403)

        booking_id = request.POST.get("booking_id")
        delivery_cost = request.POST.get("delivery_cost")

        if not booking_id or not delivery_cost:
            return JsonResponse({"detail": "Booking ID and delivery cost are required."}, status=400)

        try:
            booking = Booking.objects.get(pk=booking_id)
        except Booking.DoesNotExist:
            return JsonResponse({"detail": "Booking not found."}, status=404)

        try:
            delivery_cost = float(delivery_cost)
        except ValueError:
            return JsonResponse({"detail": "Invalid delivery cost value."}, status=400)

        # Retrieve the user's active subscription
        active_subscription = UserSubscription.objects.filter(
            user=booking.client,
            subscription_status='active',
            is_active=True
        ).exclude(plan__name=SubscriptionPlan.FREE).first()

        if not active_subscription:
            return JsonResponse({"detail": "Client does not have an active subscription."}, status=400)

        # Calculate the insurance payment
        if active_subscription.plan.name == SubscriptionPlan.PREMIUM:
            insurance_payment = 150000  # Insurance payment for premium clients
        else:
            insurance_payment = 0  # No insurance payment for basic clients

        # Update the delivery cost and total delivery cost
        booking.delivery_cost = delivery_cost
        booking.total_delivery_cost = booking.delivery_cost + insurance_payment
        booking.save()

        # Success response
        messages.success(request, f"Delivery cost updated for booking {booking_id}. Total cost: {booking.total_delivery_cost}")
        return redirect("admin-booking-list")  # Replace with your actual URL name




# from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# @method_decorator(admin_required, name='dispatch')
# class BookingAdminListView(View):

#     def get(self, request, *args, **kwargs):
#         if not request.user.is_superuser:
#             raise PermissionDenied("Only superusers can view all bookings.")

#         queryset = Booking.objects.all()
#         bookings_data = []

#         for booking in queryset:
#             # Get client subscription details
#             client_subscription = UserSubscription.objects.filter(
#                 user=booking.client, subscription_status='active', is_active=True
#             ).first()
#             client_subscription_name = client_subscription.plan.name if client_subscription else "No active subscription"

#             # Prepare booking data with client subscription details
#             booking_data = {
#                 "booking_details": booking,
#                 "client_details": {
#                     "username": booking.client.username,
#                     "email": booking.client.email,
#                     "current_subscription_plan": client_subscription_name,
#                 },
#             }
#             bookings_data.append(booking_data)

#         # Pagination
#         page = request.GET.get('page', 1)
#         paginator = Paginator(bookings_data, 5)  # Show 10 bookings per page

#         try:
#             bookings_data = paginator.page(page)
#         except PageNotAnInteger:
#             bookings_data = paginator.page(1)
#         except EmptyPage:
#             bookings_data = paginator.page(paginator.num_pages)

#         # Render the data into a template
#         return render(request, "booking/admin_booking_list.html", {
#             "bookings_data": bookings_data
#         })
