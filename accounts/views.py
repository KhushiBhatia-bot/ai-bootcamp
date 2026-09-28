from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout as auth_logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect('blog:dashboard')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to the platform, {user.username}! Your account has been created.")
            return redirect('blog:dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password. Please try again.")
        return super().form_invalid(form)


def logout_view(request):
    auth_logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('blog:home')


@login_required
def profile_view(request):
    # Ensure profile exists
    profile = getattr(request.user, 'profile', None)
    if not profile:
        from .models import Profile
        profile = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, instance=profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please check the form for errors.")
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)

    context = {
        'u_form': u_form,
        'p_form': p_form,
    }
    return render(request, 'accounts/profile.html', context)
