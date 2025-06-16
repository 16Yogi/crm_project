# apps/views/components/teamTarget.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum, Q
from django.utils import timezone
from django.http import JsonResponse
from apps.models import Client, Profile, Target, Payment
import calendar
import json

@login_required
def teamTarget(request):
    """Team Target page - Show team targets exactly like UI"""
    
    print(f"\n🎯 TEAM TARGET PAGE REQUEST:")
    print(f"User: {request.user.username}")
    print(f"Is Staff: {request.user.is_staff}")
    
    # Check if user has permission to view team targets
    if not request.user.is_staff:
        print("❌ User is not staff, redirecting to own target")
        return redirect('mytarget')
    
    # Get filters
    selected_employee = request.GET.get('team_member', 'all')
    month_filter = request.GET.get('month_filter')
    
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
    
    print(f"Filters: Employee={selected_employee}, Month={month_filter}")
    
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
        # Regular employee - redirect to own target
        print("Regular employee, redirecting to own target")
        return redirect('mytarget')
    
    # Get team members data for the table (exactly like UI)
    team_members_data = []
    
    if selected_employee == 'all':
        # Show all team members
        employees_to_show = all_employees
    else:
        # Filter by specific employee
        try:
            selected_user = User.objects.get(username=selected_employee)
            if request.user.is_superuser or selected_user in all_employees:
                employees_to_show = [selected_user]
                print(f"Filtered to employee: {selected_employee}")
            else:
                employees_to_show = all_employees
                print(f"Employee {selected_employee} not accessible, showing all team")
        except User.DoesNotExist:
            employees_to_show = all_employees
            print(f"Employee {selected_employee} not found, showing all team")
    
    # Calculate data for each team member (exactly like UI shows)
    for employee in employees_to_show:
        try:
            profile = Profile.objects.get(user=employee)
            designation = profile.designation or 'Employee'
        except Profile.DoesNotExist:
            designation = 'Employee'
        
        # Get target for this month (from Target model or Profile default)
        try:
            target = Target.objects.get(
                user=employee,
                month=filter_month,
                year=filter_year
            )
            target_amount = target.amount
        except Target.DoesNotExist:
            # Use default target from profile
            target_amount = profile.monthly_target if profile else 21000.00
        
        # Calculate received amount (achievements)
        # From payments this month
        monthly_payments = Payment.objects.filter(
            client__agent=employee,
            payment_date__year=filter_year,
            payment_date__month=filter_month,
            is_verified=True
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # From completed clients this month  
        monthly_completed = Client.objects.filter(
            agent=employee,
            project_status='Completed',
            created_at__year=filter_year,
            created_at__month=filter_month
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Total received amount
        received_amount = monthly_payments + monthly_completed
        
        # Calculate percentage
        achievement_percentage = (received_amount / target_amount * 100) if target_amount > 0 else 0
        
        # Determine status exactly like UI
        if achievement_percentage >= 100:
            status = 'Achieved'
            status_class = 'achieved'
        elif achievement_percentage >= 50:
            status = '(Active)'
            status_class = 'active'
        else:
            status = '(Active)'
            status_class = 'active'
        
        team_members_data.append({
            'user': employee,
            'name': employee.get_full_name() or employee.username,
            'username': employee.username,
            'designation': designation,
            'target_amount': target_amount,
            'received_amount': received_amount,
            'achievement_percentage': round(achievement_percentage, 1),
            'status': status,
            'status_class': status_class,
        })
    
    # Sort by name/designation
    team_members_data.sort(key=lambda x: (x['designation'], x['name']))
    
    # Prepare team members list for dropdown (exactly like UI)
    team_members_list = []
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
    
    # Sort team members for dropdown
    team_members_list.sort(key=lambda x: (x['designation'], x['name']))
    
    # Month name
    month_name = calendar.month_name[filter_month]
    
    print(f"Team members data: {len(team_members_data)}")
    
    context = {
        'team_members_data': team_members_data,
        'team_members_list': team_members_list,
        'selected_employee': selected_employee,
        'month_filter': month_filter,
        'filter_month_name': month_name,
        'filter_year': filter_year,
        'user_role': user_profile.designation if user_profile else 'Admin',
        'is_admin': request.user.is_superuser,
        'is_team_leader': user_profile.designation == 'Team Leader' if user_profile else False,
    }
    
    return render(request, 'component/teamTarget.html', context)


@login_required
def add_team_target(request):
    """Add or update target for team member"""
    
    print(f"\n🎯 ADD_TEAM_TARGET REQUEST:")
    print(f"Method: {request.method}")
    print(f"User: {request.user.username}")
    print(f"Is Ajax: {request.headers.get('X-Requested-With') == 'XMLHttpRequest'}")
    
    if request.method == 'POST':
        try:
            # Print raw request body for debugging
            print(f"Raw body: {request.body}")
            
            data = json.loads(request.body)
            print(f"Parsed data: {data}")
            
            username = data.get('username')
            target_amount = float(data.get('target_amount', 0))
            month = int(data.get('month'))
            year = int(data.get('year'))
            
            print(f"Target details: {username}, ₹{target_amount}, {month}/{year}")
            
            # Check if user exists
            try:
                target_user = User.objects.get(username=username)
                print(f"Target user found: {target_user}")
            except User.DoesNotExist:
                print(f"❌ User not found: {username}")
                return JsonResponse({
                    'success': False,
                    'message': f'User {username} not found'
                })
            
            # Check permissions
            if not request.user.is_staff:
                print("❌ User is not staff")
                return JsonResponse({
                    'success': False,
                    'message': 'Permission denied'
                })
            
            # Create or update target
            target, created = Target.objects.update_or_create(
                user=target_user,
                month=month,
                year=year,
                defaults={
                    'amount': target_amount,
                    'set_by': request.user
                }
            )
            
            print(f"✅ Target {'created' if created else 'updated'}: {target}")
            
            return JsonResponse({
                'success': True,
                'message': f"Target {'created' if created else 'updated'} successfully",
                'target_amount': target_amount
            })
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            })
        except ValueError as e:
            print(f"❌ Value error: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Invalid data format'
            })
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    print("❌ Invalid request method")
    return JsonResponse({'success': False, 'message': 'Invalid request method'})