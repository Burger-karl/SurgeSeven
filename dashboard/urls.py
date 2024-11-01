from django.urls import path
from .views import client_dashboard_view, truck_owner_dashboard_view, AboutView, ClientHomeView, TruckOwnerHomeView, AdminHomeView

urlpatterns = [
    path('client/home/', ClientHomeView.as_view(), name='client_home'),
    path('truck-owner/home/', TruckOwnerHomeView.as_view(), name='truck_owner_home'),
    path('home/', AdminHomeView.as_view(), name='admin_home'),
    path('about/', AboutView.as_view(), name='about'),
    
    path('client-dashboard/', client_dashboard_view, name='client_dashboard'),
    path('truck-owner-dashboard/', truck_owner_dashboard_view, name='truck_owner_dashboard'),
]
