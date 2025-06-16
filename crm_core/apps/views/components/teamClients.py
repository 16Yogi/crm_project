from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.http import JsonResponse
from apps.models import Client, Profile, Payment
import calendar
import json


@login_required
def teamClient(request):
    """Team Client page - Admin/Team Lead can see all team members' clients"""
    
    print(f"\n👥 TEAM CLIENT PAGE REQUEST:")
    print(f"User: {request.user.username}")
    print(f"Is Staff: {request.user.is_staff}")
    
    # Check if user has permission to view team clients
    if not request.user.is_staff:
        print("❌ User is not staff, redirecting to own clients")
        return redirect('myclient')
    
    # Get filters
    selected_employee = request.GET.get('team_member', 'all')
    month_filter = request.GET.get('month_filter')
    status_filter = request.GET.get('status_filter', 'all')
    
    # Current date logic
    current_date = timezone.now()
    if month_filter:
        try:
            year, month = month_filter.split('-')
            filter_year = int(year)
            filter_month = int(month)
        except:
            filter_year = current_date.year
            filter_month = current_date.month
            month_filter = f"{filter_year}-{filter_month:02d}"
    else:
        filter_year = current_date.year
        filter_month = current_date.month
        month_filter = f"{filter_year}-{filter_month:02d}"
    
    print(f"Filters: Employee={selected_employee}, Month={month_filter}, Status={status_filter}")
    
    # Get user's profile to determine hierarchy
    try:
        user_profile = Profile.objects.get(user=request.user)
        print(f"User designation: {user_profile.designation}")
    except Profile.DoesNotExist:
        user_profile = None
        print("No user profile found")
    
    # Determine which team members to show based on user role
    if request.user.is_superuser:
        # Admin can see everyone
        all_employees = User.objects.filter(is_active=True).exclude(id=request.user.id)
        print(f"Admin view: showing all {all_employees.count()} employees")
    elif user_profile and user_profile.designation == 'Team Leader':
        # Team Lead can see their subordinates
        subordinates = Profile.objects.filter(reporting_to=user_profile)
        all_employees = [sub.user for sub in subordinates]
        print(f"Team Lead view: showing {len(all_employees)} subordinates")
    else:
        # Regular employee - redirect to own clients
        print("Regular employee, redirecting to own clients")
        return redirect('myclient')
    
    # Start with all team clients
    if selected_employee == 'all':
        if request.user.is_superuser:
            team_clients = Client.objects.all()
        else:
            # Team leader sees subordinates' clients
            team_clients = Client.objects.filter(agent__in=all_employees)
    else:
        # Filter by specific employee
        try:
            selected_user = User.objects.get(username=selected_employee)
            if request.user.is_superuser or selected_user in all_employees:
                team_clients = Client.objects.filter(agent=selected_user)
                print(f"Filtered to employee: {selected_employee}")
            else:
                team_clients = Client.objects.filter(agent__in=all_employees)
                print(f"Employee {selected_employee} not accessible, showing all team")
        except User.DoesNotExist:
            team_clients = Client.objects.filter(agent__in=all_employees)
            print(f"Employee {selected_employee} not found, showing all team")
    
    # Apply month filter
    if month_filter:
        team_clients = team_clients.filter(
            created_at__year=filter_year,
            created_at__month=filter_month
        )
    
    # Apply status filter
    if status_filter != 'all':
        team_clients = team_clients.filter(project_status=status_filter)
    
    # Order by latest
    team_clients = team_clients.select_related('agent').order_by('-created_at')
    
    print(f"Total clients after filters: {team_clients.count()}")
    
    # Calculate status counts for sidebar
    status_counts = {}
    
    # Get all team clients for this month (without status filter for counts)
    if selected_employee == 'all':
        if request.user.is_superuser:
            count_clients = Client.objects.filter(
                created_at__year=filter_year,
                created_at__month=filter_month
            )
        else:
            count_clients = Client.objects.filter(
                agent__in=all_employees,
                created_at__year=filter_year,
                created_at__month=filter_month
            )
    else:
        try:
            selected_user = User.objects.get(username=selected_employee)
            count_clients = Client.objects.filter(
                agent=selected_user,
                created_at__year=filter_year,
                created_at__month=filter_month
            )
        except User.DoesNotExist:
            count_clients = Client.objects.filter(
                agent__in=all_employees,
                created_at__year=filter_year,
                created_at__month=filter_month
            )
    
    # Calculate counts
    status_counts = {
        'all': count_clients.count(),
        'New Lead': count_clients.filter(project_status='New Lead').count(),
        'In Progress': count_clients.filter(project_status='In Progress').count(),
        'Follow Up': count_clients.filter(project_status='Follow Up').count(),
        'Completed': count_clients.filter(project_status='Completed').count(),
        'Cancelled': count_clients.filter(project_status='Cancelled').count(),
        'Not Interested': count_clients.filter(project_status='Not Interested').count(),
    }
    
    # Calculate special categories
    status_counts['metalized'] = count_clients.exclude(project_status__in=['Cancelled', 'Not Interested']).count()
    status_counts['callback'] = count_clients.filter(project_status='Follow Up').count()
    status_counts['transferred'] = 0  # Will need transfer history if implemented
    status_counts['already_paid'] = count_clients.filter(project_status='Completed').count()
    
    # Prepare team members list with designations
    team_members_list = []
    if request.user.is_superuser:
        for emp in all_employees:
            try:
                profile = Profile.objects.get(user=emp)
                designation = profile.designation or 'Employee'
            except Profile.DoesNotExist:
                designation = 'Employee'
            
            team_members_list.append({
                'user': emp,
                'username': emp.username,
                'name': emp.get_full_name() or emp.username,
                'designation': designation,
            })
    else:
        for emp in all_employees:
            try:
                profile = Profile.objects.get(user=emp)
                designation = profile.designation or 'Employee'
            except Profile.DoesNotExist:
                designation = 'Employee'
            
            team_members_list.append({
                'user': emp,
                'username': emp.username,
                'name': emp.get_full_name() or emp.username,
                'designation': designation,
            })
    
    # Sort team members
    team_members_list.sort(key=lambda x: (x['designation'], x['name']))
    
    # Month name
    import calendar
    month_name = calendar.month_name[filter_month]
    
    # Determine current page title
    if status_filter == 'Not Interested':
        page_title = "All Not Interested"
    elif status_filter == 'Completed':
        page_title = "All Completed"
    elif status_filter == 'New Lead':
        page_title = "All New Leads"
    elif status_filter == 'In Progress':
        page_title = "All In Progress"
    elif status_filter == 'Follow Up':
        page_title = "All Follow Up"
    elif status_filter == 'Cancelled':
        page_title = "All Cancelled"
    else:
        page_title = "All Clients"
    
    print(f"Status counts: {status_counts}")
    print(f"Team members: {len(team_members_list)}")
    
    context = {
        'team_clients': team_clients,
        'team_members_list': team_members_list,
        'selected_employee': selected_employee,
        'month_filter': month_filter,
        'status_filter': status_filter,
        'filter_month_name': month_name,
        'filter_year': filter_year,
        'status_counts': status_counts,
        'page_title': page_title,
        'user_role': user_profile.designation if user_profile else 'Admin',
        'is_admin': request.user.is_superuser,
        'is_team_leader': user_profile.designation == 'Team Leader' if user_profile else False,
    }
    
    return render(request, 'component/teamClients.html', context)