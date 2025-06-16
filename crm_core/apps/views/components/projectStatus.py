# apps/views/components/projectStatus.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum, Q, Count
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from apps.models import Client, Profile, Payment
import calendar
import json
import csv

@login_required
def projectstatus(request):
    """Project Status page - Show all project statuses with month filter"""
    
    print(f"\n📊 PROJECT STATUS PAGE REQUEST:")
    print(f"User: {request.user.username}")
    print(f"Is Staff: {request.user.is_staff}")
    
    # Get filters
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
    
    print(f"Filters: Month={month_filter}")
    
    # Get user's profile to determine access
    try:
        user_profile = Profile.objects.get(user=request.user)
        print(f"User designation: {user_profile.designation}")
    except Profile.DoesNotExist:
        user_profile = None
        print("No user profile found")
    
    # Determine which clients to show based on user role
    if request.user.is_superuser:
        # Admin can see all clients
        base_clients = Client.objects.all()
        print(f"Admin view: showing all clients")
    elif user_profile and user_profile.designation == 'Team Leader':
        # Team Lead can see their subordinates' clients
        subordinates = Profile.objects.filter(reporting_to=user_profile)
        subordinate_users = [sub.user for sub in subordinates]
        subordinate_users.append(request.user)  # Include self
        base_clients = Client.objects.filter(agent__in=subordinate_users)
        print(f"Team Lead view: showing team clients")
    else:
        # Regular employee sees only own clients
        base_clients = Client.objects.filter(agent=request.user)
        print("Employee view: showing own clients")
    
    # Apply month filter
    filtered_clients = base_clients.filter(
        created_at__year=filter_year,
        created_at__month=filter_month
    )
    
    # Get all project data for the table
    project_data = []
    
    for client in filtered_clients.select_related('agent').order_by('-created_at'):
        # Get agent profile
        try:
            agent_profile = Profile.objects.get(user=client.agent)
            agent_designation = agent_profile.designation or 'Employee'
        except Profile.DoesNotExist:
            agent_designation = 'Employee'
        
        # Get payment details for this client
        total_payments = Payment.objects.filter(
            client=client,
            is_verified=True
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Calculate verification details
        verification_status = "Verified" if total_payments > 0 else "Pending"
        verification_amount = total_payments
        
        # Determine frontend and backend status based on project status
        status_mapping = {
            'New': {'frontend': 'New Lead', 'backend': 'Pending'},
            'Contacted': {'frontend': 'In Progress', 'backend': 'Active'},
            'In Progress': {'frontend': 'In Progress', 'backend': 'Active'},
            'Completed': {'frontend': 'Completed', 'backend': 'Live'},
            'Cancelled': {'frontend': 'Cancelled', 'backend': 'Cancelled'},
        }
        
        current_status = client.project_status
        if current_status in status_mapping:
            frontend_status = status_mapping[current_status]['frontend']
            backend_status = status_mapping[current_status]['backend']
        else:
            frontend_status = current_status
            backend_status = current_status
        
        project_data.append({
            'client': client,
            'agent_name': client.agent.get_full_name() or client.agent.username,
            'agent_designation': agent_designation,
            'customer_name': client.customer_name,
            'business_name': client.business_name or 'N/A',
            'project_type': client.project_type,
            'total_amount': client.total_amount,
            'advance_amount': client.advance_amount,
            'total_payments': total_payments,
            'remaining_amount': client.total_amount - total_payments,
            'verification_status': verification_status,
            'verification_amount': verification_amount,
            'frontend_status': frontend_status,
            'backend_status': backend_status,
            'created_date': client.created_at,
            'month_year': f"{calendar.month_name[filter_month]} {filter_year}",
            'phone_number': client.primary_phone,
            'business_address': client.business_address or 'N/A'
        })
    
    # Calculate summary statistics
    total_projects = len(project_data)
    total_amount = sum([p['total_amount'] for p in project_data])
    total_payments = sum([p['total_payments'] for p in project_data])
    total_pending = sum([p['remaining_amount'] for p in project_data])
    
    # Status wise counts
    status_counts = {
        'new': len([p for p in project_data if 'New' in p['frontend_status']]),
        'in_progress': len([p for p in project_data if 'Progress' in p['frontend_status']]),
        'completed': len([p for p in project_data if 'Completed' in p['frontend_status']]),
        'cancelled': len([p for p in project_data if 'Cancelled' in p['frontend_status']]),
    }
    
    # Month name for display
    month_name = calendar.month_name[filter_month]
    
    print(f"Total projects: {total_projects}")
    print(f"Status counts: {status_counts}")
    
    context = {
        'project_data': project_data,
        'month_filter': month_filter,
        'filter_month_name': month_name,
        'filter_year': filter_year,
        'total_projects': total_projects,
        'total_amount': total_amount,
        'total_payments': total_payments,
        'total_pending': total_pending,
        'status_counts': status_counts,
        'user_role': user_profile.designation if user_profile else 'Admin',
        'is_admin': request.user.is_superuser,
        'is_team_leader': user_profile.designation == 'Team Leader' if user_profile else False,
    }
    
    return render(request, 'component/projectStatus.html', context)


@login_required
def update_project_status(request):
    """Update project status via AJAX"""
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            client_id = data.get('client_id')
            new_status = data.get('status')
            
            print(f"Updating project status: {client_id} -> {new_status}")
            
            # Get the client
            client = Client.objects.get(client_id=client_id)
            
            # Check permissions
            if not (request.user.is_staff or client.agent == request.user):
                return JsonResponse({
                    'success': False,
                    'message': 'Permission denied'
                })
            
            # Update status
            client.project_status = new_status
            client.save()
            
            print(f"✅ Status updated successfully")
            
            return JsonResponse({
                'success': True,
                'message': 'Status updated successfully'
            })
            
        except Client.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Client not found'
            })
        except Exception as e:
            print(f"❌ Error updating status: {e}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def export_project_status(request):
    """Export project status to CSV"""
    
    month_filter = request.GET.get('month_filter')
    
    # Get same filtered data as main view
    current_date = timezone.now()
    if month_filter:
        try:
            year, month = month_filter.split('-')
            filter_year = int(year)
            filter_month = int(month)
        except:
            filter_year = current_date.year
            filter_month = current_date.month
    else:
        filter_year = current_date.year
        filter_month = current_date.month
    
    # Get filtered clients
    if request.user.is_superuser:
        base_clients = Client.objects.all()
    else:
        base_clients = Client.objects.filter(agent=request.user)
    
    filtered_clients = base_clients.filter(
        created_at__year=filter_year,
        created_at__month=filter_month
    )
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="project_status_{month_filter}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Customer Name', 'Business Name', 'Agent', 'Project Type',
        'Total Amount', 'Payments Received', 'Remaining Amount',
        'Frontend Status', 'Backend Status', 'Created Date'
    ])
    
    # Add data rows
    for client in filtered_clients.select_related('agent'):
        total_payments = Payment.objects.filter(
            client=client,
            is_verified=True
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        writer.writerow([
            client.customer_name,
            client.business_name or 'N/A',
            client.agent.get_full_name() or client.agent.username,
            client.project_type,
            client.total_amount,
            total_payments,
            client.total_amount - total_payments,
            client.project_status,
            client.project_status,
            client.created_at.strftime('%Y-%m-%d %H:%M')
        ])
    
    return response


@login_required
def view_project_details(request):
    """View project details via AJAX"""
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            client_id = data.get('client_id')
            
            # Get the client
            client = Client.objects.get(client_id=client_id)
            
            # Check permissions
            if not (request.user.is_staff or client.agent == request.user):
                return JsonResponse({
                    'success': False,
                    'message': 'Permission denied'
                })
            
            # Get payment details
            payments = Payment.objects.filter(client=client).order_by('-payment_date')
            payment_list = []
            for payment in payments:
                payment_list.append({
                    'amount': float(payment.amount),
                    'date': payment.payment_date.strftime('%Y-%m-%d'),
                    'method': payment.payment_method,
                    'notes': payment.notes or ''
                })
            
            client_details = {
                'customer_name': client.customer_name,
                'business_name': client.business_name or 'N/A',
                'phone': client.primary_phone,
                'email': client.business_email or 'N/A',
                'address': client.business_address or 'N/A',
                'project_type': client.project_type,
                'total_amount': float(client.total_amount),
                'advance_amount': float(client.advance_amount),
                'status': client.project_status,
                'created_date': client.created_at.strftime('%Y-%m-%d %H:%M'),
                'payments': payment_list
            }
            
            return JsonResponse({
                'success': True,
                'client': client_details
            })
            
        except Client.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Client not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})
    # return render(request,"component/projectStatus.html")