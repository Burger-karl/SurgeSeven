from django.urls import path
from . import views

urlpatterns = [
    path('delivery-schedules/create/', views.create_delivery_schedule_view, name='create_delivery_schedule'),
    path('delivery-schedules/', views.delivery_schedule_list_view, name='delivery_schedule_list'),
    path('delivery-histories/', views.delivery_history_view, name='delivery_history_list'),
    path('delivery-documents/', views.delivery_document_list_view, name='delivery_document_list'),
    
    # FOR ADMINUSER
    # path('delivery-schedules/<int:pk>/update-status/', views.update_delivery_schedule_status_view, name='update_delivery_schedule_status'),
]
