"""
Permission System for Hotel Review Platform
Custom decorators and mixins for role-based access control
"""

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Q

from apps.reviews.models import Hotel
from apps.reviews.user_profile import UserProfile


# Role-based decorators
def role_required(allowed_roles):
    """
    Decorator that restricts access to users with specific roles
    
    Args:
        allowed_roles: List of allowed roles ['admin', 'manager', 'viewer']
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, 'profile'):
                messages.error(request, 'User profile not found. Please contact administrator.')
                return redirect('authentication:unauthorized')
            
            user_role = request.user.profile.role
            if user_role not in allowed_roles:
                messages.error(request, f'Access denied. Required role: {", ".join(allowed_roles)}')
                return redirect('authentication:unauthorized')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def admin_required(view_func):
    """Decorator that restricts access to admin users only"""
    return role_required(['admin'])(view_func)


def manager_or_admin_required(view_func):
    """Decorator that restricts access to managers and admins"""
    return role_required(['admin', 'manager'])(view_func)


def hotel_access_required(view_func):
    """
    Decorator that ensures user has access to the hotel specified in the request
    Expects hotel_id in URL parameters or form data
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'User profile not found.')
            return redirect('authentication:unauthorized')
        
        profile = request.user.profile
        
        # Admin users have access to all hotels
        if profile.role == 'admin':
            return view_func(request, *args, **kwargs)
        
        # Get hotel_id from URL parameters or form data
        hotel_id = kwargs.get('hotel_id') or request.GET.get('hotel_id') or request.POST.get('hotel_id')
        
        if not hotel_id:
            # If no specific hotel is requested, proceed (will be filtered in view)
            return view_func(request, *args, **kwargs)
        
        try:
            hotel = get_object_or_404(Hotel, id=hotel_id)
            if not profile.can_access_hotel(hotel):
                messages.error(request, f'You do not have access to {hotel.name}.')
                return redirect('authentication:unauthorized')
        except Exception:
            messages.error(request, 'Invalid hotel specified.')
            return redirect('dashboard:home')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def api_permission_required(allowed_roles):
    """
    Decorator for API views that returns JSON error responses
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            if not hasattr(request.user, 'profile'):
                return JsonResponse({'error': 'User profile not found'}, status=403)
            
            user_role = request.user.profile.role
            if user_role not in allowed_roles:
                return JsonResponse({
                    'error': f'Access denied. Required role: {", ".join(allowed_roles)}'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


# Class-based view mixins
class RoleRequiredMixin(LoginRequiredMixin):
    """
    Mixin that restricts access to users with specific roles
    """
    allowed_roles = []
    permission_denied_message = "You don't have permission to access this page."
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'User profile not found. Please contact administrator.')
            return redirect('authentication:unauthorized')
        
        user_role = request.user.profile.role
        if user_role not in self.allowed_roles:
            messages.error(request, self.permission_denied_message)
            return redirect('authentication:unauthorized')
        
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(RoleRequiredMixin):
    """Mixin that restricts access to admin users only"""
    allowed_roles = ['admin']
    permission_denied_message = "Administrator access required."


class ManagerOrAdminRequiredMixin(RoleRequiredMixin):
    """Mixin that restricts access to managers and admins"""
    allowed_roles = ['admin', 'manager']
    permission_denied_message = "Manager or administrator access required."


class HotelAccessMixin(LoginRequiredMixin):
    """
    Mixin that filters data based on user's hotel access
    Provides hotel filtering for views
    """
    
    def get_user_hotels(self):
        """Get hotels that the current user can access"""
        if not hasattr(self.request.user, 'profile'):
            return Hotel.objects.none()
        
        return self.request.user.profile.get_accessible_hotels()
    
    def filter_queryset_by_hotel(self, queryset, hotel_field='hotel'):
        """
        Filter queryset to only include data from accessible hotels
        
        Args:
            queryset: The queryset to filter
            hotel_field: The field name that relates to Hotel model
        """
        user_hotels = self.get_user_hotels()
        
        if not user_hotels.exists():
            return queryset.none()
        
        # Build the filter dynamically
        filter_kwargs = {f'{hotel_field}__in': user_hotels}
        return queryset.filter(**filter_kwargs)
    
    def get_context_data(self, **kwargs):
        """Add user's accessible hotels to context"""
        context = super().get_context_data(**kwargs)
        context['user_accessible_hotels'] = self.get_user_hotels()
        context['user_profile'] = getattr(self.request.user, 'profile', None)
        return context


class APIPermissionMixin:
    """
    Mixin for API views that provides role-based access control
    """
    allowed_roles = []
    
    def check_permissions(self, request):
        """Check if user has required permissions"""
        if not request.user.is_authenticated:
            return False, {'error': 'Authentication required', 'status': 401}
        
        if not hasattr(request.user, 'profile'):
            return False, {'error': 'User profile not found', 'status': 403}
        
        user_role = request.user.profile.role
        if self.allowed_roles and user_role not in self.allowed_roles:
            return False, {
                'error': f'Access denied. Required role: {", ".join(self.allowed_roles)}',
                'status': 403
            }
        
        return True, None
    
    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to check permissions"""
        has_permission, error_response = self.check_permissions(request)
        
        if not has_permission:
            return JsonResponse(
                {'error': error_response['error']}, 
                status=error_response['status']
            )
        
        return super().dispatch(request, *args, **kwargs)


# Utility functions for permission checking
def user_can_access_hotel(user, hotel):
    """Check if user can access a specific hotel"""
    if not hasattr(user, 'profile'):
        return False
    
    return user.profile.can_access_hotel(hotel)


def filter_hotels_for_user(user, queryset=None):
    """Filter hotels based on user access"""
    if queryset is None:
        queryset = Hotel.objects.all()
    
    if not hasattr(user, 'profile'):
        return queryset.none()
    
    accessible_hotels = user.profile.get_accessible_hotels()
    return queryset.filter(id__in=accessible_hotels.values_list('id', flat=True))


def get_user_role(user):
    """Get user's role safely"""
    if hasattr(user, 'profile') and user.profile:
        return user.profile.role
    return None


def user_has_permission(user, permission_type):
    """
    Check if user has specific permission
    
    Args:
        user: Django User instance
        permission_type: String - 'manage_hotels', 'view_analytics', 'upload_reviews', 'delete_data'
    """
    if not hasattr(user, 'profile'):
        return False
    
    profile = user.profile
    
    permission_map = {
        'manage_hotels': profile.can_manage_hotels,
        'view_analytics': profile.can_view_analytics,
        'upload_reviews': profile.can_upload_reviews,
        'delete_data': profile.can_delete_data,
    }
    
    return permission_map.get(permission_type, False)


# Context processor for templates
def auth_context_processor(request):
    """
    Context processor to add authentication-related data to all templates
    """
    context = {
        'user_profile': None,
        'user_role': None,
        'user_accessible_hotels': [],
        'user_permissions': {},
    }
    
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        profile = request.user.profile
        context.update({
            'user_profile': profile,
            'user_role': profile.role,
            'user_accessible_hotels': profile.get_accessible_hotels(),
            'user_permissions': {
                'can_manage_hotels': profile.can_manage_hotels,
                'can_view_analytics': profile.can_view_analytics,
                'can_upload_reviews': profile.can_upload_reviews,
                'can_delete_data': profile.can_delete_data,
            }
        })
    
    return context
