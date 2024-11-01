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

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist



# class RegisterView(CreateView):
#     form_class = RegisterForm
#     template_name = 'users/register.html'
#     success_url = reverse_lazy('verify-email')

#     def form_valid(self, form):
#         user = form.save(commit=False)  # Prepare user object but don't save yet
#         user_type = form.cleaned_data.get('user_type')

#         # Set user permissions based on the user type
#         if user_type == 'admin':
#             user.is_staff = True
#             user.is_superuser = True
#         elif user_type == 'client' or user_type == 'truck_owner':
#             user.is_staff = False
#             user.is_superuser = False

#         user.save()  # Save the user object now to ensure it's saved before creating related objects

#         # If the user is a client, assign the default free subscription plan
#         if user_type == 'client':
#             free_plan = SubscriptionPlan.objects.get(name='free')
#             UserSubscription.objects.create(
#                 user=user,  # Now user is saved, so this should work fine
#                 plan=free_plan,
#                 is_active=False,
#                 subscription_status='inactive'
#             )

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


# class VerifyEmailView(FormView):
#     form_class = OTPForm
#     template_name = 'users/verify_email.html'
#     success_url = reverse_lazy('login')

#     def form_valid(self, form):
#         otp = form.cleaned_data.get('otp')
#         try:
#             otp_obj = OTP.objects.get(otp=otp)
#             otp_obj.user.is_active = True
#             otp_obj.user.save()
#             otp_obj.delete()
#         except OTP.DoesNotExist:
#             form.add_error('otp', 'Invalid OTP')
#             return self.form_invalid(form)
#         return super().form_valid(form)

# class LoginView(FormView):
#     form_class = LoginForm
#     template_name = 'users/login.html'
#     success_url = reverse_lazy('profile-create')

#     def form_valid(self, form):
#         email = form.cleaned_data.get('email')
#         password = form.cleaned_data.get('password')
#         user = authenticate(self.request, email=email, password=password)
#         if user:
#             login(self.request, user)
#             return super().form_valid(form)
#         form.add_error(None, 'Invalid credentials')
#         return self.form_invalid(form)


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

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist



class RegisterView(View):
    form_class = RegisterForm
    template_name = 'users/register.html'
    
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            user_data = {
                'email': form.cleaned_data['email'],
                'username': form.cleaned_data['username'],
                'password1': form.cleaned_data['password1'],
                'password2': form.cleaned_data['password2'],
                'user_type': form.cleaned_data['user_type']
            }

            # Set is_staff and is_superuser flags for admin users
            if user_data['user_type'] == 'admin':
                user_data['is_staff'] = True
                user_data['is_superuser'] = True

            # Store user data in session until verification
            request.session['user_data'] = user_data

            # Generate and send OTP
            otp = get_random_string(length=6, allowed_chars='0123456789')
            request.session['otp'] = otp
            send_mail(
                'Verify your email',
                f'Your OTP is {otp}',
                'from@example.com',
                [user_data['email']],
            )
            messages.success(request, "An OTP has been sent to your email for verification.")
            return redirect('verify-email')
        return render(request, self.template_name, {'form': form})



class VerifyEmailView(FormView):
    form_class = OTPForm
    template_name = 'users/verify_email.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        otp = form.cleaned_data.get('otp')
        session_otp = self.request.session.get('otp')
        if otp == session_otp:
            user_data = self.request.session.get('user_data')
            if not user_data:
                form.add_error(None, 'User data not found. Please register again.')
                return self.form_invalid(form)

            # Create user in the database now
            user = User.objects.create_user(
                email=user_data['email'],
                username=user_data['username'],
                password=user_data['password1'],
                
                user_type=user_data['user_type'],
                is_verified=True,
                is_active=True  # Activate after verification
            )

            # Assign free subscription if user is a client
            if user.user_type == 'client':
                free_plan = SubscriptionPlan.objects.get(name='free')
                UserSubscription.objects.create(
                    user=user,
                    plan=free_plan,
                    is_active=False,
                    subscription_status='inactive'
                )

            # Clear session data
            del self.request.session['user_data']
            del self.request.session['otp']

            messages.success(self.request, "Your email has been verified! You can now log in.")
            return super().form_valid(form)
        else:
            form.add_error('otp', 'Invalid OTP')
            return self.form_invalid(form)


class LoginView(FormView):
    form_class = LoginForm
    template_name = 'users/login.html'
    success_url = reverse_lazy('profile-create')

    def form_valid(self, form):
        email = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password')
        user = authenticate(self.request, email=email, password=password)
        if user:
            if user.is_verified:
                login(self.request, user)
                return super().form_valid(form)
            else:
                form.add_error(None, 'Your account is not verified. Please verify your email.')
                return self.form_invalid(form)
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

