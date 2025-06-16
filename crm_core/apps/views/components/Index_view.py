from django.shortcuts import redirect

def index_view(request):
    if request.user.is_authenticated:
        return redirect('startcalls')  # Changed to match the URL name in urls.py
    else:
        return redirect('Login')  # This is correct as per urls.py 