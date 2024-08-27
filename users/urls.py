from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify-email'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/create/', views.ProfileCreateView.as_view(), name='profile-create'),
    path('profile/update/', views.ProfileUpdateView.as_view(), name='profile-update'),


    # path('admin/create-user/', views.admin_create_user, name='admin-create-user'),
]
