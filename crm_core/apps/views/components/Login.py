# views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def Login(request):
    # If user is already logged in, redirect them to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard') # Assuming your dashboard URL name is 'dashboard'
    
    # If form has been submitted (i.e., 'POST' request received)
    if request.method == 'POST':
        # Extract username and password from the form
        username_from_form = request.POST.get('username')
        password_from_form = request.POST.get('password')
        
        # Check if username and password are not empty
        if not username_from_form or not password_from_form:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'component/Login.html')
        
        # Verify the user using Django's authenticate function
        # This will check if there's a user with this username and password in the database
        user = authenticate(request, username=username_from_form, password=password_from_form)
        
        # If user is valid (authenticate returned a user object)
        if user is not None:
            # Now log the user into the system
            # This will create a session and store the user's ID in the session
            login(request, user)
            
            # (Optional) Show a success message
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect user to dashboard page
            return redirect('startcalls/') # You need to create a URL with name 'dashboard'
        
        # If user is not valid (authenticate returned None)
        else:
            # Show an error message
            messages.error(request, 'Invalid username or password. Please try again.')
            # Keep the user on the login page
            return render(request, 'component/Login.html')
    
    # If this is a 'GET' request (i.e., user just visited the page)
    # Just show the login page
    return render(request, 'component/Login.html')