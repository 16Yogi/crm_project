    
# views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db import models  # Add this import
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, date
from apps.models import Client, Profile
import traceback

@login_required
def myclient(request):
    """My Clients page with data fetching and month filter"""
    
    print(f"\n🔥 MY CLIENT PAGE REQUEST:")
    print(f"User: {request.user.username}")
    print(f"GET params: {request.GET}")
    
    # Get current user's clients
    clients = Client.objects.filter(agent=request.user)
    
    # Month filter logic
    month_filter = request.GET.get('month_filter')
    current_month = timezone.now().strftime('%Y-%m')  # Default to current month
    
    if month_filter:
        try:
            # Parse the month filter (format: YYYY-MM)
            year, month = month_filter.split('-')
            clients = clients.filter(
                created_at__year=int(year),
                created_at__month=int(month)
            )
            print(f"Filtering by month: {month_filter}")
        except (ValueError, IndexError):
            # If invalid format, show all clients
            month_filter = None
            print("Invalid month filter format")
    else:
        # Default: show current month's clients
        month_filter = current_month
        current_date = timezone.now()
        clients = clients.filter(
            created_at__year=current_date.year,
            created_at__month=current_date.month
        )
    
    # Order by latest first
    clients = clients.order_by('-created_at')
    
    print(f"Total clients found: {clients.count()}")
    
    # Get user profile for additional data
    user_profile = None
    try:
        user_profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        print("User profile not found")
    
    # Calculate some stats for debugging
    total_clients = Client.objects.filter(agent=request.user).count()
    completed_clients = Client.objects.filter(
        agent=request.user, 
        project_status='Completed'
    ).count()
    
    print(f"User stats - Total: {total_clients}, Completed: {completed_clients}")
    
    context = {
        'clients': clients,
        'month_filter': month_filter,
        'total_clients': total_clients,
        'completed_clients': completed_clients,
        'user_profile': user_profile,
    }
    
    return render(request, 'component/myClients.html', context)
