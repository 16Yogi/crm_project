# apps/views/components/addTeamMember.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from apps.models import TeamMember, Profile
import json

@login_required
def addTeamMember(request):
    """Add Team Member with debug functionality"""
    
    print(f"\n👥 ADD TEAM MEMBER REQUEST:")
    print(f"Method: {request.method}")
    print(f"User: {request.user.username}")
    print(f"Is Staff: {request.user.is_staff}")
    
    if request.method == 'POST':
        print("📝 POST Data received:")
        print(f"POST data: {request.POST}")
        
        # Get form data
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        role = request.POST.get('role', '').strip()
        department = request.POST.get('department', '').strip()
        
        print(f"Parsed data:")
        print(f"  Name: '{name}'")
        print(f"  Email: '{email}'")
        print(f"  Phone: '{phone}'")
        print(f"  Role: '{role}'")
        print(f"  Department: '{department}'")
        
        # Validate required fields
        if not all([name, email, phone, role, department]):
            missing_fields = []
            if not name: missing_fields.append('Name')
            if not email: missing_fields.append('Email')
            if not phone: missing_fields.append('Phone')
            if not role: missing_fields.append('Role')
            if not department: missing_fields.append('Department')
            
            error_msg = f'Missing required fields: {", ".join(missing_fields)}'
            print(f"❌ Validation Error: {error_msg}")
            messages.error(request, error_msg)
            
            context = {
                'roles': ['Executive', 'Team Leader', 'Manager', 'Admin'],
                'departments': ['Sales', 'Marketing', 'Support', 'Management'],
                'form_data': {
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'role': role,
                    'department': department
                }
            }
            return render(request, 'component/add_team_member.html', context)
        
        # Check if email already exists
        if TeamMember.objects.filter(email=email).exists():
            error_msg = 'Team member with this email already exists!'
            print(f"❌ Email exists: {error_msg}")
            messages.error(request, error_msg)
            
            context = {
                'roles': ['Executive', 'Team Leader', 'Manager', 'Admin'],
                'departments': ['Sales', 'Marketing', 'Support', 'Management'],
                'form_data': {
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'role': role,
                    'department': department
                }
            }
            return render(request, 'component/add_team_member.html', context)
        
        # Create new team member
        try:
            print("🔄 Creating team member...")
            
            team_member = TeamMember.objects.create(
                name=name,
                email=email,
                phone=phone,
                role=role,
                department=department,
                is_active=True  # Ensure it's active
            )
            
            print(f"✅ Team member created successfully:")
            print(f"  ID: {team_member.id}")
            print(f"  Name: {team_member.name}")
            print(f"  Email: {team_member.email}")
            print(f"  Role: {team_member.role}")
            
            # Also create a User account if needed (optional)
            try:
                # Check if user with this email exists
                if not User.objects.filter(email=email).exists():
                    user = User.objects.create_user(
                        username=email.split('@')[0],  # Use email prefix as username
                        email=email,
                        first_name=name.split()[0] if name.split() else name,
                        last_name=' '.join(name.split()[1:]) if len(name.split()) > 1 else '',
                        is_active=True
                    )
                    
                    # Create Profile for the user
                    Profile.objects.create(
                        user=user,
                        phone_number=phone,
                        designation=role,
                        account_status='Active'
                    )
                    
                    print(f"✅ User account also created: {user.username}")
                else:
                    print("ℹ️ User account already exists for this email")
                    
            except Exception as user_error:
                print(f"⚠️ Warning: Could not create user account: {user_error}")
                # Continue anyway, team member is still created
            
            messages.success(request, f'Team member "{name}" added successfully!')
            print("✅ Success message added, redirecting...")
            
            return redirect('teamClient')  # या जो भी आपका target page है
            
        except Exception as e:
            error_msg = f'Error adding team member: {str(e)}'
            print(f"❌ Database Error: {error_msg}")
            messages.error(request, error_msg)
            
            context = {
                'roles': ['Executive', 'Team Leader', 'Manager', 'Admin'],
                'departments': ['Sales', 'Marketing', 'Support', 'Management'],
                'form_data': {
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'role': role,
                    'department': department
                }
            }
            return render(request, 'component/add_team_member.html', context)
    
    # GET request - show form
    print("📄 Showing add team member form")
    
    context = {
        'roles': ['Executive', 'Team Leader', 'Manager', 'Admin'],
        'departments': ['Sales', 'Marketing', 'Support', 'Management']
    }
    return render(request, 'component/add_team_member.html', context)


@login_required
def teamMemberList(request):
    """List all team members for debugging"""
    
    print(f"\n👥 TEAM MEMBER LIST REQUEST:")
    
    team_members = TeamMember.objects.all().order_by('-created_at')
    
    print(f"Total team members found: {team_members.count()}")
    
    for member in team_members:
        print(f"  - {member.name} ({member.email}) - {member.role}")
    
    context = {
        'team_members': team_members
    }
    
    return render(request, 'component/team_member_list.html', context)


@login_required  
def deleteTeamMember(request, member_id):
    """Delete team member"""
    
    if request.method == 'POST':
        try:
            team_member = TeamMember.objects.get(id=member_id)
            member_name = team_member.name
            team_member.delete()
            
            messages.success(request, f'Team member "{member_name}" deleted successfully!')
            print(f"✅ Team member deleted: {member_name}")
            
        except TeamMember.DoesNotExist:
            messages.error(request, 'Team member not found!')
            print("❌ Team member not found for deletion")
        except Exception as e:
            messages.error(request, f'Error deleting team member: {str(e)}')
            print(f"❌ Error deleting team member: {e}")
    
    return redirect('team_member_list')


# Debug function to check database
def debug_team_members(request):
    """Debug function to check team members in database"""
    
    print(f"\n🔍 DEBUG TEAM MEMBERS:")
    print(f"TeamMember model exists: {TeamMember._meta.db_table}")
    
    try:
        total_count = TeamMember.objects.count()
        print(f"Total team members in database: {total_count}")
        
        if total_count > 0:
            print("Recent team members:")
            for member in TeamMember.objects.all()[:5]:
                print(f"  ID: {member.id}, Name: {member.name}, Email: {member.email}")
        else:
            print("No team members found in database")
            
    except Exception as e:
        print(f"Database error: {e}")
    
    return JsonResponse({
        'total_count': TeamMember.objects.count(),
        'debug': 'Check console for details'
    })