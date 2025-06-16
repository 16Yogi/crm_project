# apps/views/components/Profileview.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserUpdateForm, ProfileUpdateForm
from apps.models import Profile  # <-- Make sure Profile model is imported

@login_required
def profile_view(request):
    # ---- Make changes here ----
    # Use Profile.objects.get_or_create()
    # This will either fetch the existing profile, or create a new one if it doesn't exist.
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    # If the profile was just created, you can show a message if you want (Optional)
    if created:
        messages.info(request, 'Your profile was created. Please fill in your details.')
    # ---- End of changes ----
    
    # If the form has been submitted
    if request.method == 'POST':
        # Get form data from request.POST and file data from request.FILES
        u_form = UserUpdateForm(request.POST, instance=request.user)
        # Now use the 'profile' variable, which will always exist
        p_form = ProfileUpdateForm(request.POST,
                                  request.FILES,
                                  instance=profile)
        
        # Validate both forms
        if u_form.is_valid() and p_form.is_valid():
            # If both are valid, save them
            u_form.save()
            p_form.save()
            
            messages.success(request, 'Your profile has been updated successfully!')
            
            # Redirect back to the same page. Make sure the URL name is correct.
            # Assuming your URL name is 'profile_view'.
            return redirect('profile_view')
    
    # If this is a GET request
    else:
        u_form = UserUpdateForm(instance=request.user)
        # Use the 'profile' variable here too
        p_form = ProfileUpdateForm(instance=profile)
    
    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    
    # Template name 'component/Profile.html' is correct
    return render(request, 'component/Profile.html', context)