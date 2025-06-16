# accounts/forms.py

from apps.models import Profile
from django import forms
from django.contrib.auth.models import User


# This form will update User model fields
class UserUpdateForm(forms.ModelForm):
    # We want to make email required
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email'] # Cannot change username

# This form will update Profile model fields
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone_number','branch_address', 'designation']