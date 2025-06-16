# apps/views/components/startingCalling.py
# Simple working version

from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.timezone import now
from django.db import transaction
from apps.models import Client
from decimal import Decimal
import traceback

@login_required
def startcalls(request):
    """Main dashboard view"""
    try:
        today = now().date()
        my_clients_today = Client.objects.filter(
            agent=request.user,
            created_at__date=today
        ).order_by('-created_at')
        
        context = {
            'clients_today': my_clients_today,
        }
        return render(request, 'component/startcalling.html', context)
        
    except Exception as e:
        print(f"Error in startcalls: {e}")
        return render(request, 'component/startcalling.html', {'clients_today': []})

@login_required
@require_POST
def add_client(request):
    """Add new client via AJAX"""
    
    # Debug print करें
    print(f"\n🔥 ADD CLIENT REQUEST:")
    print(f"User: {request.user.username}")
    print(f"POST data: {dict(request.POST)}")
    
    try:
        # Get form data
        customer_name = request.POST.get('customer_name', '').strip()
        business_name = request.POST.get('business_name', '').strip()
        business_address = request.POST.get('business_address', '').strip()
        primary_phone = request.POST.get('primary_phone', '').strip()
        secondary_phone = request.POST.get('secondary_phone', '').strip()
        business_email = request.POST.get('business_email', '').strip()
        business_gst_number = request.POST.get('business_gst_number', '').strip()
        industry_type = request.POST.get('industry_type', '').strip()
        project_type = request.POST.get('project_type', '').strip()
        project_handover_date = request.POST.get('project_handover_date', '').strip()
        remark = request.POST.get('remark', '').strip()
        project_status = request.POST.get('project_status', 'New')
        total_amount = request.POST.get('total_amount', '').strip()
        advance_amount = request.POST.get('advance_amount', '0').strip()
        
        print(f"Customer name: '{customer_name}'")
        print(f"Phone: '{primary_phone}'")
        print(f"Total amount: '{total_amount}'")
        
        # Basic validation
        if not customer_name:
            return JsonResponse({
                'status': 'error',
                'message': 'Customer name is required'
            })
        
        if not primary_phone:
            return JsonResponse({
                'status': 'error', 
                'message': 'Primary phone is required'
            })
        
        if not total_amount:
            return JsonResponse({
                'status': 'error',
                'message': 'Total amount is required'
            })
        
        # Convert amounts
        try:
            total_amt = Decimal(total_amount)
            advance_amt = Decimal(advance_amount) if advance_amount else Decimal('0')
        except:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid amount format'
            })
        
        # Check duplicate phone
        if Client.objects.filter(primary_phone=primary_phone).exists():
            return JsonResponse({
                'status': 'warning',
                'message': f'Phone number {primary_phone} already exists'
            })
        
        # Parse date
        handover_date = None
        if project_handover_date:
            try:
                from datetime import datetime
                handover_date = datetime.strptime(project_handover_date, '%Y-%m-%d').date()
            except:
                handover_date = None
        
        print(f"Creating client with data...")
        
        # Create client
        with transaction.atomic():
            new_client = Client.objects.create(
                agent=request.user,
                customer_name=customer_name,
                business_name=business_name if business_name else None,
                business_address=business_address if business_address else None,
                primary_phone=primary_phone,
                secondary_phone=secondary_phone if secondary_phone else None,
                business_email=business_email if business_email else None,
                business_gst_number=business_gst_number if business_gst_number else None,
                industry_type=industry_type if industry_type else None,
                project_type=project_type if project_type else 'Web Design & Development',
                project_handover_date=handover_date,
                remark=remark if remark else None,
                project_status=project_status,
                total_amount=total_amt,
                advance_amount=advance_amt,
            )
            
            print(f"✅ Client created successfully: {new_client.client_id}")
            
            return JsonResponse({
                'status': 'success',
                'message': f"Client '{new_client.customer_name}' added successfully!",
                'client_id': str(new_client.client_id),
                'client': {
                    'id': str(new_client.client_id),
                    'customer_name': new_client.customer_name,
                    'primary_phone': new_client.primary_phone,
                    'project_status': new_client.project_status,
                    'business_name': new_client.business_name or '',
                    'total_amount': str(new_client.total_amount),
                    'advance_amount': str(new_client.advance_amount),
                    'created_at': new_client.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            })
        
    except Exception as e:
        print(f"❌ Error creating client: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error: {str(e)}'
        })

@login_required
def test_client_creation(request):
    """Test endpoint"""
    if request.method == 'POST':
        try:
            print(f"🧪 Testing client creation for user: {request.user.username}")
            
            test_client = Client.objects.create(
                agent=request.user,
                customer_name="Test Client",
                primary_phone="9999999999",
                project_type="Test Project",
                total_amount=Decimal('1000.00'),
                advance_amount=Decimal('100.00'),
                project_status="New"
            )
            
            print(f"✅ Test client created: {test_client.client_id}")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Test client created with ID: {test_client.client_id}'
            })
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return JsonResponse({
                'status': 'error',
                'message': f'Test failed: {str(e)}'
            })
    
    return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'})