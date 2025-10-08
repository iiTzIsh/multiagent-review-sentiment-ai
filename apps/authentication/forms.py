"""
Authentication Forms for Hotel Review Platform
Professional forms for login, registration, and profile management
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from apps.reviews.models import Hotel
from apps.authentication.models import UserProfile


class LoginForm(AuthenticationForm):
    """Professional login form with enhanced styling"""
    
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter username',
            'autofocus': True,
            'autocomplete': 'username',
        }),
        help_text="Enter your username"
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter password',
            'autocomplete': 'current-password',
        }),
        help_text="Enter your password"
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label="Keep me logged in for 2 weeks"
    )
    
    class Meta:
        fields = ['username', 'password', 'remember_me']


class UserRegistrationForm(UserCreationForm):
    """Professional user registration form for admin use"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address',
        }),
        help_text="Valid email address for account notifications"
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name',
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name',
        })
    )
    
    hotel = forms.ModelChoiceField(
        queryset=Hotel.objects.all(),
        required=False,
        empty_label="Select Hotel (Optional)",
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        help_text="Primary hotel association"
    )
    
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        initial='viewer',
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        help_text="User role determines access permissions"
    )
    
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter phone number',
        })
    )
    
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter department/position',
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter username',
                'autofocus': True,
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Update password field styling
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter password',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password',
        })
        
        # Update help texts
        self.fields['username'].help_text = "Unique username for login (letters, digits and @/./+/-/_ only)"
        self.fields['password1'].help_text = "Minimum 8 characters with letters and numbers"
        self.fields['password2'].help_text = "Enter the same password as before, for verification"
    
    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email
    
    def save(self, commit=True):
        """Save user and create profile"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            
            # Create or update profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.hotel = self.cleaned_data.get('hotel')
            profile.role = self.cleaned_data['role']
            profile.phone_number = self.cleaned_data.get('phone_number', '')
            profile.department = self.cleaned_data.get('department', '')
            profile.save()
        
        return user


class UserProfileForm(forms.ModelForm):
    """User profile editing form"""
    
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name',
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name',
        })
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address',
        })
    )
    
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter phone number',
        })
    )
    
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter department/position',
        })
    )
    
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'department']
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
    
    def save_user_data(self, user):
        """Save user model data"""
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.save()


class PasswordChangeForm(forms.Form):
    """Password change form"""
    
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter current password',
        }),
        help_text="Enter your current password"
    )
    
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password',
        }),
        help_text="Minimum 8 characters with letters and numbers"
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
        }),
        help_text="Enter the same password as above, for verification"
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        """Validate current password"""
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise ValidationError("Current password is incorrect.")
        return current_password
    
    def clean(self):
        """Validate password confirmation"""
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise ValidationError("New passwords do not match.")
            
            if len(new_password) < 8:
                raise ValidationError("Password must be at least 8 characters long.")
        
        return cleaned_data
