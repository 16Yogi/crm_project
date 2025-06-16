# apps/views/components/clientTransfer.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from django.contrib import messages
from apps.models import Client, Profile, ClientTransfer
import json
from datetime import datetime, timedelta

# First, add this model to your models.py:
# class ClientTransfer(models.Model):
#     client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='transfers')
#     from_agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transferred_clients')
#     to_agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_clients')
#     transferred_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_transfers')
#     transfer_date = models.DateTimeField(auto_now_add=True)
#     reason = models.TextField(blank=True, null=True)
#     notes = models.TextField(blank=True, null=True)
#     is_active = models.BooleanField(default=True)
#     
#     class Meta:
#         ordering = ['-transfer_date']
#     
#     def __str__(self):
#         return f"{self.client.customer_name} transferred from {self.from_agent.username} to {self.to_agent.username}"

@login_required
def transferClient(request):
    """Transfer Client page - Admin/Team Leader can transfer clients"""
    
    print(f"\n🔄 CLIENT TRANSFER PAGE REQUEST:")
    print(f"User: {request.user.username}")
    print(f"Is Staff: {request.user.is_staff}")
    
    # Check permissions
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to transfer clients.')
        return redirect('dashboard')
    
    # Get user's profile to determine hierarchy
    try:
        user_profile = Profile.objects.get(user=request.user)
        print(f"User designation: {user_profile.designation}")
    except Profile.DoesNotExist:
        user_profile = None
        print("No user profile found")
    
    # Get all active users for transfer options
    if request.user.is_superuser:
        # Admin can transfer between any users
        all_agents = User.objects.filter(is_active=True).exclude(id=request.user.id)
        all_clients = Client.objects.all()
    elif user_profile and user_profile.designation == 'Team Leader':
        # Team Lead can transfer within their team
        subordinates = Profile.objects.filter(reporting_to=user_profile)
        subordinate_users = [sub.user for sub in subordinates]
        subordinate_users.append(request.user)  # Include self
        all_agents = subordinate_users
        all_clients = Client.objects.filter(agent__in=subordinate_users)
    else:
        messages.error(request, 'You do not have permission to transfer clients.')
        return redirect('dashboard')
    
    # Get recent transfers (last 30 days)
    recent_transfers = ClientTransfer.objects.filter(
        transfer_date__gte=timezone.now() - timedelta(days=30),
        is_active=True
    ).select_related('client', 'from_agent', 'to_agent', 'transferred_by')[:20]
    
    context = {
        'all_agents': all_agents,
        'all_clients': all_clients,
        'recent_transfers': recent_transfers,
        'user_role': user_profile.designation if user_profile else 'Admin',
        'is_admin': request.user.is_superuser,
    }
    
    return render(request, 'component/ClientTransfer.html', context)


@login_required
def executeClientTransfer(request):
    """Execute client transfer via AJAX"""
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            client_id = data.get('client_id')
            to_agent_id = data.get('to_agent_id')
            reason = data.get('reason', '').strip()
            notes = data.get('notes', '').strip()
            
            print(f"🔄 Transfer request:")
            print(f"  Client ID: {client_id}")
            print(f"  To Agent ID: {to_agent_id}")
            print(f"  Reason: {reason}")
            
            # Validate data
            if not all([client_id, to_agent_id]):
                return JsonResponse({
                    'success': False,
                    'message': 'Client and target agent are required'
                })
            
            # Get client
            try:
                client = Client.objects.get(client_id=client_id)
            except Client.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Client not found'
                })
            
            # Get target agent
            try:
                to_agent = User.objects.get(id=to_agent_id, is_active=True)
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Target agent not found'
                })
            
            # Check if trying to transfer to same agent
            if client.agent.id == int(to_agent_id):
                return JsonResponse({
                    'success': False,
                    'message': 'Client is already assigned to this agent'
                })
            
            # Check permissions
            if not request.user.is_staff:
                return JsonResponse({
                    'success': False,
                    'message': 'Permission denied'
                })
            
            # Store original agent
            from_agent = client.agent
            
            # Create transfer record
            transfer = ClientTransfer.objects.create(
                client=client,
                from_agent=from_agent,
                to_agent=to_agent,
                transferred_by=request.user,
                reason=reason,
                notes=notes
            )
            
            # Update client's agent
            client.agent = to_agent
            client.save()
            
            print(f"✅ Client transferred successfully:")
            print(f"  From: {from_agent.username}")
            print(f"  To: {to_agent.username}")
            print(f"  Client: {client.customer_name}")
            
            return JsonResponse({
                'success': True,
                'message': f'Client "{client.customer_name}" transferred successfully from {from_agent.get_full_name() or from_agent.username} to {to_agent.get_full_name() or to_agent.username}',
                'transfer_id': transfer.id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            })
        except Exception as e:
            print(f"❌ Transfer error: {e}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def getClientsByAgent(request):
    """Get clients by agent via AJAX"""
    
    if request.method == 'GET':
        agent_id = request.GET.get('agent_id')
        
        if not agent_id:
            return JsonResponse({
                'success': False,
                'message': 'Agent ID is required'
            })
        
        try:
            agent = User.objects.get(id=agent_id, is_active=True)
            clients = Client.objects.filter(agent=agent).order_by('-created_at')
            
            client_list = []
            for client in clients:
                client_list.append({
                    'id': str(client.client_id),
                    'name': client.customer_name,
                    'business': client.business_name or 'N/A',
                    'phone': client.primary_phone,
                    'status': client.project_status,
                    'created_date': client.created_at.strftime('%Y-%m-%d')
                })
            
            return JsonResponse({
                'success': True,
                'clients': client_list,
                'agent_name': agent.get_full_name() or agent.username
            })
            
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Agent not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def getTransferredClients(request):
    """Get clients transferred to current user today"""
    
    today = timezone.now().date()
    
    # Get clients transferred to current user today
    transferred_today = ClientTransfer.objects.filter(
        to_agent=request.user,
        transfer_date__date=today,
        is_active=True
    ).select_related('client', 'from_agent')
    
    transferred_clients = []
    for transfer in transferred_today:
        transferred_clients.append({
            'client': transfer.client,
            'from_agent': transfer.from_agent,
            'transfer_date': transfer.transfer_date,
            'reason': transfer.reason or 'No reason provided'
        })
    
    return JsonResponse({
        'success': True,
        'transferred_clients': [
            {
                'customer_name': tc['client'].customer_name,
                'primary_phone': tc['client'].primary_phone,
                'project_status': tc['client'].project_status,
                'from_agent': tc['from_agent'].get_full_name() or tc['from_agent'].username,
                'transfer_time': tc['transfer_date'].strftime('%H:%M'),
                'reason': tc['reason']
            }
            for tc in transferred_clients
        ]
    })


@login_required
def reverseClientTransfer(request):
    """Reverse a client transfer"""
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            transfer_id = data.get('transfer_id')
            
            if not transfer_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Transfer ID is required'
                })
            
            # Get transfer record
            transfer = ClientTransfer.objects.get(id=transfer_id, is_active=True)
            
            # Check permissions
            if not request.user.is_staff:
                return JsonResponse({
                    'success': False,
                    'message': 'Permission denied'
                })
            
            # Reverse the transfer
            client = transfer.client
            original_agent = transfer.from_agent
            
            # Update client's agent back to original
            client.agent = original_agent
            client.save()
            
            # Mark transfer as inactive
            transfer.is_active = False
            transfer.save()
            
            # Create reverse transfer record
            ClientTransfer.objects.create(
                client=client,
                from_agent=transfer.to_agent,
                to_agent=original_agent,
                transferred_by=request.user,
                reason=f"Reversed transfer #{transfer_id}",
                notes=f"Transfer reversed by {request.user.username}"
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Transfer reversed successfully. Client "{client.customer_name}" is back with {original_agent.get_full_name() or original_agent.username}'
            })
            
        except ClientTransfer.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Transfer record not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})