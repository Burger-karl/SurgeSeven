from django.urls import path
from .views import client_dashboard_view, truck_owner_dashboard_view, HomeView, AboutView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('about/', AboutView.as_view(), name='about'),
    path('client-dashboard/', client_dashboard_view, name='client-dashboard'),
    path('truck-owner-dashboard/', truck_owner_dashboard_view, name='truck_owner_dashboard'),
]
