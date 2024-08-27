from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import DeliverySchedule, DeliveryHistory, DeliveryDocument
from booking.models import Booking
from datetime import datetime
from .forms import DeliveryScheduleForm

# Create your views here.

@login_required
def create_delivery_schedule_view(request):
    if request.method == 'POST':
        form = DeliveryScheduleForm(request.POST)
        if form.is_valid():
            booking_id = form.cleaned_data.get('booking_id')
            booking = get_object_or_404(Booking, id=booking_id)

            if booking.booking_status != 'active' or not booking.payment_completed:
                messages.error(request, 'Booking is not confirmed or paid for.')
                return redirect('create_delivery_schedule')

            scheduled_date = datetime.now().date()

            delivery_schedule = DeliverySchedule.objects.create(
                booking=booking,
                scheduled_date=scheduled_date
            )

            DeliveryHistory.objects.create(
                booking=booking,
                delivery_date=scheduled_date,
                status='pending'
            )

            messages.success(request, 'Delivery Schedule created successfully.')
            return redirect('delivery_schedule_list')
    else:
        form = DeliveryScheduleForm()
    
    return render(request, 'delivery/create_schedule.html', {'form': form})


@login_required
def delivery_schedule_list_view(request):
    user = request.user
    schedules = DeliverySchedule.objects.filter(booking__client=user, booking__booking_status='active')
    return render(request, 'delivery/schedule_list.html', {'schedules': schedules})


@login_required
def delivery_history_view(request):
    user = request.user
    histories = DeliveryHistory.objects.filter(booking__client=user, status='delivered')
    return render(request, 'delivery/history_list.html', {'histories': histories})


@login_required
def delivery_document_list_view(request):
    documents = DeliveryDocument.objects.filter(booking__client=request.user)
    return render(request, 'delivery/document_list.html', {'documents': documents})



# FOR ADMINUSER

# from django.http import HttpResponseForbidden

# @login_required
# def update_delivery_schedule_status_view(request, pk):
#     if not request.user.is_superuser:
#         return HttpResponseForbidden("Only superusers can update delivery status.")
    
#     delivery_schedule = get_object_or_404(DeliverySchedule, pk=pk)
#     delivery_schedule.status = 'delivered'
#     delivery_schedule.save()

#     # Update the corresponding DeliveryHistory status
#     delivery_history = DeliveryHistory.objects.filter(booking=delivery_schedule.booking).first()
#     if delivery_history:
#         delivery_history.status = 'delivered'
#         delivery_history.delivery_date = datetime.now().date()  # Update delivery date
#         delivery_history.save()

#     messages.success(request, 'Delivery schedule status updated to delivered.')
#     return redirect('delivery_schedule_list')

