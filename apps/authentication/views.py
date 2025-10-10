"""
Authentication Views for Hotel Review Platform
Handles login, logout, registration with role-based access control
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.db import transaction
import json

from apps.reviews.models import Hotel
from apps.authentication.models import UserProfile
from apps.authentication.forms import UserRegistrationForm


def login_view(request):
    """Professional login page with error handling"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    # Set session expiry based on remember me
                    if not remember_me:
                        request.session.set_expiry(0)  # Browser close
                    else:
                        request.session.set_expiry(1209600)  # 2 weeks
                    
                    # Update last login IP (handle profile safely)
                    try:
                        if hasattr(user, 'profile') and user.profile:
                            user.profile.last_login_ip = get_client_ip(request)
                            user.profile.save()
                        else:
                            # Create profile if it doesn't exist
                            profile, created = UserProfile.objects.get_or_create(user=user)
                            profile.last_login_ip = get_client_ip(request)
                            profile.save()
                    except Exception as e:
                        # Log the error but don't prevent login
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Could not update last_login_ip for user {user.username}: {e}")
                    
                    messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                    
                    # Redirect to intended page or dashboard
                    next_url = request.GET.get('next', 'dashboard:home')
                    return redirect(next_url)
                else:
                    messages.error(request, 'Your account is disabled. Please contact your administrator.')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please enter both username and password.')
    
    return render(request, 'auth/login.html')


def logout_view(request):
    """Logout with confirmation message"""
    if request.user.is_authenticated:
        username = request.user.get_full_name() or request.user.username
        logout(request)
        messages.success(request, f'You have been successfully logged out. Goodbye, {username}!')
    
    return redirect('auth:login')


@login_required
def register_view(request):
    """User registration (admin only)"""
    # Check if user can create accounts
    if not (request.user.is_superuser or 
            (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
        messages.error(request, 'You do not have permission to create user accounts.')
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Save the user and profile
                    user = form.save()
                    messages.success(request, f'User account created successfully for {user.get_full_name() or user.username}!')
                    return redirect('auth:register')
            except Exception as e:
                messages.error(request, f'Error creating user: {str(e)}')
    else:
        form = UserRegistrationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'auth/register.html', context)


@login_required
def profile_view(request):
    """User profile management"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update profile information
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        profile.phone_number = request.POST.get('phone_number', '')
        profile.department = request.POST.get('department', '')
        profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('auth:profile')
    
    context = {
        'profile': profile,
        'accessible_hotels': profile.get_accessible_hotels(),
    }
    return render(request, 'auth/profile.html', context)


@login_required
@require_http_methods(["POST"])
def change_password_view(request):
    """Change user password"""
    current_password = request.POST.get('current_password')
    new_password = request.POST.get('new_password')
    confirm_password = request.POST.get('confirm_password')
    
    if not all([current_password, new_password, confirm_password]):
        messages.error(request, 'All password fields are required.')
        return redirect('auth:profile')
    
    if not request.user.check_password(current_password):
        messages.error(request, 'Current password is incorrect.')
        return redirect('auth:profile')
    
    if new_password != confirm_password:
        messages.error(request, 'New passwords do not match.')
        return redirect('auth:profile')
    
    if len(new_password) < 8:
        messages.error(request, 'Password must be at least 8 characters long.')
        return redirect('auth:profile')
    
    request.user.set_password(new_password)
    request.user.save()
    
    # Re-login user to maintain session
    login(request, request.user)
    
    messages.success(request, 'Password changed successfully!')
    return redirect('auth:profile')


@login_required
def user_list_view(request):
    """List all users (admin only)"""
    if not (request.user.is_superuser or 
            (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
        messages.error(request, 'You do not have permission to view user list.')
        return redirect('dashboard:home')
    
    users = User.objects.select_related('profile', 'profile__hotel').order_by('username')
    
    context = {
        'users': users,
    }
    return render(request, 'auth/user_list.html', context)


@login_required
@csrf_exempt
def toggle_user_status(request):
    """Toggle user active status (admin only)"""
    if not (request.user.is_superuser or 
            (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            user = get_object_or_404(User, id=user_id)
            
            # Don't allow disabling superusers
            if user.is_superuser:
                return JsonResponse({'success': False, 'error': 'Cannot disable superuser'})
            
            user.is_active = not user.is_active
            user.save()
            
            return JsonResponse({
                'success': True, 
                'is_active': user.is_active,
                'message': f'User {"activated" if user.is_active else "deactivated"} successfully'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def unauthorized_view(request):
    """Unauthorized access page"""
    return render(request, 'auth/unauthorized.html', status=403)