# apps/views/components/myTarget.py (Python file only)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import models
from django.utils import timezone
from apps.models import Target, Client, Profile
import calendar

@login_required
def mytarget(request):
    """My Target page with monthly target tracking"""
    
    print(f"\n🎯 MY TARGET PAGE REQUEST:")
    print(f"User: {request.user.username}")
    
    # Month filter logic
    month_filter = request.GET.get('month_filter')
    current_date = timezone.now()
    
    if month_filter:
        try:
            # Parse format: YYYY-MM
            year, month = month_filter.split('-')
            filter_year = int(year)
            filter_month = int(month)
        except:
            # Default to current month
            filter_year = current_date.year
            filter_month = current_date.month
            month_filter = f"{filter_year}-{filter_month:02d}"
    else:
        # Default to current month
        filter_year = current_date.year
        filter_month = current_date.month
        month_filter = f"{filter_year}-{filter_month:02d}"
    
    print(f"Filter: Year={filter_year}, Month={filter_month}")
    
    # Get user's targets for the selected month
    user_targets = Target.objects.filter(
        user=request.user,
        year=filter_year,
        month=filter_month
    )
    
    print(f"Found {user_targets.count()} targets in Target model")
    
    # Calculate achieved amount for the month
    achieved_amount = Client.objects.filter(
        agent=request.user,
        project_status='Completed',
        created_at__year=filter_year,
        created_at__month=filter_month
    ).aggregate(
        total=models.Sum('total_amount')
    )['total'] or 0
    
    print(f"Achieved amount: ₹{achieved_amount}")
    
    # Prepare targets data for template
    targets_data = []
    
    if user_targets.exists():
        print("Processing targets from Target model...")
        
        for target in user_targets:
            print(f"Processing target: {target.amount}")
            
            # Get who assigned this target
            assigned_by = "Self Assigned"
            if target.set_by:
                if target.set_by != request.user:
                    assigned_by = target.set_by.get_full_name() or target.set_by.username
                    # Add designation if available
                    try:
                        profile = Profile.objects.get(user=target.set_by)
                        if profile.designation:
                            assigned_by += f" ({profile.designation})"
                    except Profile.DoesNotExist:
                        pass
            
            # Calculate achievement percentage
            achievement_percentage = 0
            if target.amount > 0:
                achievement_percentage = (float(achieved_amount) / float(target.amount)) * 100
            
            # Determine status
            if achievement_percentage >= 100:
                status = "Achieved"
            elif achievement_percentage >= 75:
                status = "On Track"
            elif achievement_percentage >= 50:
                status = "Behind"
            else:
                status = "Critical"
            
            # Month name
            month_name = calendar.month_name[target.month]
            
            target_data = {
                'target': target,
                'assigned_by': assigned_by,
                'target_amount': target.amount,
                'achieved_amount': achieved_amount,
                'remaining_amount': target.amount - achieved_amount,
                'achievement_percentage': round(achievement_percentage, 1),
                'status': status,
                'month_name': month_name,
                'year': target.year,
                'date_added': f"Target #{target.id}",
                'is_default': False,
            }
            
            targets_data.append(target_data)
            print(f"Added target data: {target_data['target_amount']}")
    
    else:
        print("No targets found in Target model, checking Profile...")
        
        # No target found for this month
        # Check if there's a default target from Profile
        try:
            user_profile = Profile.objects.get(user=request.user)
            default_target = user_profile.monthly_target
            
            print(f"Found profile with default target: ₹{default_target}")
            
            # Get assigned by from reporting_to
            assigned_by = "System Default"
            if user_profile.reporting_to:
                assigned_by = user_profile.reporting_to.user.get_full_name() or user_profile.reporting_to.user.username
                if user_profile.reporting_to.designation:
                    assigned_by += f" ({user_profile.reporting_to.designation})"
            
            # Calculate achievement percentage
            achievement_percentage = 0
            if default_target > 0:
                achievement_percentage = (float(achieved_amount) / float(default_target)) * 100
            
            # Determine status
            if achievement_percentage >= 100:
                status = "Achieved"
            elif achievement_percentage >= 75:
                status = "On Track"
            elif achievement_percentage >= 50:
                status = "Behind"
            else:
                status = "Critical"
            
            # Month name
            month_name = calendar.month_name[filter_month]
            
            target_data = {
                'target': None,
                'assigned_by': assigned_by,
                'target_amount': default_target,
                'achieved_amount': achieved_amount,
                'remaining_amount': default_target - achieved_amount,
                'achievement_percentage': round(achievement_percentage, 1),
                'status': status,
                'month_name': month_name,
                'year': filter_year,
                'date_added': 'Default Profile Target',
                'is_default': True,
            }
            
            targets_data.append(target_data)
            print(f"Added default target data: ₹{default_target}")
            
        except Profile.DoesNotExist:
            print("❌ No profile found and no targets set")
    
    print(f"✅ Final targets_data length: {len(targets_data)}")
    
    # Additional stats
    total_targets_count = Target.objects.filter(user=request.user).count()
    
    context = {
        'targets_data': targets_data,
        'month_filter': month_filter,
        'achieved_amount': achieved_amount,
        'total_targets_count': total_targets_count,
        'filter_month_name': calendar.month_name[filter_month],
        'filter_year': filter_year,
    }
    
    print(f"Context targets_data length: {len(context['targets_data'])}")
    
    return render(request, 'component/myTarget.html', context)