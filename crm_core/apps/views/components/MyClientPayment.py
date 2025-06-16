# views.py में add करें
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import models
from django.utils import timezone
from django.http import JsonResponse
from apps.models import Client, Payment
from datetime import datetime
import json

@login_required
def myclientpayment(request):
    """My Client Payment page - Track payments for user's clients"""
    
    print(f"\n💰 MY CLIENT PAYMENT PAGE REQUEST:")
    print(f"User: {request.user.username}")
    
    # Get month filter
    month_filter = request.GET.get('month_filter')
    current_date = timezone.now()
    
    if month_filter:
        try:
            # Parse format: YYYY-MM
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
    
    print(f"Filter: Year={filter_year}, Month={filter_month}")
    
    # Get user's clients
    user_clients = Client.objects.filter(agent=request.user).order_by('-created_at')
    
    # Separate clients by payment status
    materialized_clients = []
    all_payment_done_clients = []
    
    for client in user_clients:
        # Get client's payments for the month
        client_payments = Payment.objects.filter(
            client=client,
            payment_date__year=filter_year,
            payment_date__month=filter_month
        ).order_by('-payment_date')
        
        # Calculate totals
        total_paid = client_payments.aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        # Check if fully paid (total_amount matches payments)
        if total_paid >= client.total_amount and client.total_amount > 0:
            # Fully paid client
            all_payment_done_clients.append({
                'client': client,
                'total_paid': total_paid,
                'payments': client_payments,
                'payment_status': 'Completed',
                'last_payment_date': client_payments.first().payment_date if client_payments.exists() else None,
            })
        else:
            # Materialized client (partial or no payment)
            remaining_amount = client.total_amount - total_paid
            
            materialized_clients.append({
                'client': client,
                'total_paid': total_paid,
                'remaining_amount': remaining_amount,
                'payments': client_payments,
                'payment_status': 'Pending' if total_paid == 0 else 'Partial',
                'last_payment_date': client_payments.first().payment_date if client_payments.exists() else None,
            })
    
    # Month name for display
    import calendar
    month_name = calendar.month_name[filter_month]
    
    print(f"Materialized clients: {len(materialized_clients)}")
    print(f"Fully paid clients: {len(all_payment_done_clients)}")
    
    context = {
        'materialized_clients': materialized_clients,
        'all_payment_done_clients': all_payment_done_clients,
        'month_filter': month_filter,
        'filter_month_name': month_name,
        'filter_year': filter_year,
        'total_materialized': len(materialized_clients),
        'total_completed': len(all_payment_done_clients),
    }
    
    return render(request, 'component/myClientPayment.html', context)

@login_required
def add_payment(request):
    """Add payment for a client (AJAX)"""
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            client_id = data.get('client_id')
            amount = float(data.get('amount', 0))
            payment_method = data.get('payment_method', 'Cash')
            notes = data.get('notes', '')
            
            # Get client and verify it belongs to user
            client = get_object_or_404(Client, client_id=client_id, agent=request.user)
            
            # Create payment record
            payment = Payment.objects.create(
                client=client,
                amount=amount,
                payment_method=payment_method,
                notes=notes,
                payment_date=timezone.now(),
                added_by=request.user
            )
            
            # Calculate new totals
            total_paid = Payment.objects.filter(client=client).aggregate(
                total=models.Sum('amount')
            )['total'] or 0
            
            remaining_amount = client.total_amount - total_paid
            
            return JsonResponse({
                'status': 'success',
                'message': f'Payment of ₹{amount:,.0f} added successfully',
                'payment_id': payment.id,
                'total_paid': total_paid,
                'remaining_amount': remaining_amount,
                'is_fully_paid': remaining_amount <= 0
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
def get_client_payments(request, client_id):
    """Get all payments for a specific client (AJAX)"""
    
    try:
        client = get_object_or_404(Client, client_id=client_id, agent=request.user)
        
        payments = Payment.objects.filter(client=client).order_by('-payment_date')
        
        payments_data = []
        for payment in payments:
            payments_data.append({
                'id': payment.id,
                'amount': float(payment.amount),
                'payment_method': payment.payment_method,
                'payment_date': payment.payment_date.strftime('%Y-%m-%d %H:%M'),
                'notes': payment.notes or '',
                'added_by': payment.added_by.get_full_name() if payment.added_by else 'System'
            })
        
        total_paid = payments.aggregate(total=models.Sum('amount'))['total'] or 0
        remaining_amount = client.total_amount - total_paid
        
        return JsonResponse({
            'status': 'success',
            'client_name': client.customer_name,
            'total_amount': float(client.total_amount),
            'total_paid': float(total_paid),
            'remaining_amount': float(remaining_amount),
            'payments': payments_data
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })