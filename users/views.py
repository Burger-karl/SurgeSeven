from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.views import View
from django.views.generic import CreateView, UpdateView, DetailView, FormView
from django.urls import reverse_lazy
from .forms import RegisterForm, LoginForm, OTPForm, ForgotPasswordForm, ResetPasswordForm, ProfileForm
from .models import OTP, User, PasswordResetToken, Profile
from subscriptions.models import SubscriptionPlan, UserSubscription


# class RegisterView(CreateView):
#     form_class = RegisterForm
#     template_name = 'users/register.html'
#     success_url = reverse_lazy('verify-email')

#     def form_valid(self, form):
#         user = form.save(commit=False)
#         user_type = form.cleaned_data.get('user_type')
        
#         # Handle different user types
#         if user_type == 'admin':
#             user.is_staff = True
#             user.is_superuser = True
#         elif user_type == 'client':
#             user.is_staff = False
#             user.is_superuser = False
#             # Assign default free subscription plan to new clients
#             free_plan = SubscriptionPlan.objects.get(name='free')
#             UserSubscription.objects.create(user=user, plan=free_plan, is_active=False, subscription_status='inactive')
#         elif user_type == 'truck_owner':
#             user.is_staff = False
#             user.is_superuser = False
        
#         user.save()

#         # Send OTP email
#         otp = get_random_string(length=6, allowed_chars='0123456789')
#         OTP.objects.create(user=user, otp=otp)
#         send_mail(
#             'Verify your email',
#             f'Your OTP is {otp}',
#             'from@example.com',
#             [user.email],
#         )
        
#         return super().form_valid(form)



class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('verify-email')

    def form_valid(self, form):
        user = form.save(commit=False)  # Prepare user object but don't save yet
        user_type = form.cleaned_data.get('user_type')

        # Set user permissions based on the user type
        if user_type == 'admin':
            user.is_staff = True
            user.is_superuser = True
        elif user_type == 'client' or user_type == 'truck_owner':
            user.is_staff = False
            user.is_superuser = False

        user.save()  # Save the user object now to ensure it's saved before creating related objects

        # If the user is a client, assign the default free subscription plan
        if user_type == 'client':
            free_plan = SubscriptionPlan.objects.get(name='free')
            UserSubscription.objects.create(
                user=user,  # Now user is saved, so this should work fine
                plan=free_plan,
                is_active=False,
                subscription_status='inactive'
            )

        # Send OTP email
        otp = get_random_string(length=6, allowed_chars='0123456789')
        OTP.objects.create(user=user, otp=otp)
        send_mail(
            'Verify your email',
            f'Your OTP is {otp}',
            'from@example.com',
            [user.email],
        )

        return super().form_valid(form)


class VerifyEmailView(FormView):
    form_class = OTPForm
    template_name = 'users/verify_email.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        otp = form.cleaned_data.get('otp')
        try:
            otp_obj = OTP.objects.get(otp=otp)
            otp_obj.user.is_active = True
            otp_obj.user.save()
            otp_obj.delete()
        except OTP.DoesNotExist:
            form.add_error('otp', 'Invalid OTP')
            return self.form_invalid(form)
        return super().form_valid(form)

class LoginView(FormView):
    form_class = LoginForm
    template_name = 'users/login.html'
    success_url = reverse_lazy('profile-create')

    def form_valid(self, form):
        email = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password')
        user = authenticate(self.request, email=email, password=password)
        if user:
            login(self.request, user)
            return super().form_valid(form)
        form.add_error(None, 'Invalid credentials')
        return self.form_invalid(form)

class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')

class ForgotPasswordView(FormView):
    form_class = ForgotPasswordForm
    template_name = 'users/forgot_password.html'
    success_url = reverse_lazy('reset-password')

    def form_valid(self, form):
        email = form.cleaned_data.get('email')
        users = User.objects.filter(email=email)
        if users.exists():
            for user in users:
                token = get_random_string(length=20)
                send_mail(
                    'Password Reset Request',
                    f'Use this token to reset your password: {token}',
                    'from@example.com',
                    [email],
                )
                PasswordResetToken.objects.create(user=user, token=token)
        return super().form_valid(form)

class ResetPasswordView(FormView):
    form_class = ResetPasswordForm
    template_name = 'users/reset_password.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        token = form.cleaned_data.get('token')
        new_password = form.cleaned_data.get('new_password')
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
            if reset_token.is_expired():
                form.add_error('token', 'Token is expired')
                return self.form_invalid(form)
            user = reset_token.user
            user.set_password(new_password)
            user.save()
            reset_token.delete()
        except PasswordResetToken.DoesNotExist:
            form.add_error('token', 'Invalid token')
            return self.form_invalid(form)
        return super().form_valid(form)

class ProfileCreateView(CreateView):
    form_class = ProfileForm
    template_name = 'users/profile_create.html'
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        profile = form.save(commit=False)
        profile.user = self.request.user
        profile.save()
        return super().form_valid(form)

class ProfileView(DetailView):
    model = Profile
    template_name = 'users/profile.html'
    context_object_name = 'profile'

    def get_object(self):
        return get_object_or_404(Profile, user=self.request.user)

class ProfileUpdateView(UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'users/profile_update.html'
    success_url = reverse_lazy('profile')

    def get_object(self):
        return get_object_or_404(Profile, user=self.request.user)



# For Admin

# @user_passes_test(lambda u: u.is_superuser)
# def admin_create_user(request):
#     if request.method == 'POST':
#         form = RegisterForm(request.POST)
#         if form.is_valid():
#             user = form.save(commit=False)
#             user.is_staff = True
#             user.save()
#             return redirect('user-list')
#     else:
#         form = RegisterForm()
#     return render(request, 'admin/create_user.html', {'form': form})

