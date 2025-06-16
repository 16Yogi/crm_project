# apps/urls.py - Simple working version
from django.urls import path
from apps.views.components.anotherView import another_view
from apps.views.components.startingCalling import *
from apps.views.components.myClients import *
from apps.views.components.myTarget import *
from apps.views.components.teamClients import *
from apps.views.components.teamTarget import *
from apps.views.components.projectStatus import *
from apps.views.components.admin_dashboard import *
from apps.views.components.Login import *
from apps.views.components.Index_view import index_view
from apps.views.components.Profileview import *
from apps.views.components.addTeamMember import *
from apps.views.components.MyClientPayment import *
from django.views.decorators.csrf import csrf_exempt
from apps.views.components.clientTransfer import *

urlpatterns = [
    # Add this as the first URL pattern
    path('', startcalls, name='index'),  # Root URL pattern
    # Main pages
    path('startcalls/', startcalls, name='startcalls'),
    # path('dashboard/', dashboard, name='dashboard'),
    # path('api/dashboard-stats/', get_dashboard_stats_fixed, name='get_dashboard_stats_fixed'),
    # path('api/transferred-clients/',get_transferred_clients_fixed, name='get_transferred_clients_fixed'),
    # path('api/fix-dashboard-data/',fix_dashboard_data, name='fix_dashboard_data'),
    path('another/', another_view, name='another'),
    path('myclientpayment/', myclientpayment, name='myclientpayment'),
    path('add-payment/',add_payment, name='add_payment'),
    path('get-client-payments/<str:client_id>/',get_client_payments, name='get_client_payments'),
    
    path('myclient/', myclient, name='myclient'),
    path('mytarget/', mytarget, name='mytarget'),    
    path('projectstatus/', projectstatus, name="projectstatus"),
    path('teamClients/', teamClient, name="teamClient"),
    path("teamTarget/", teamTarget, name="teamTarget"),
    path("admin_dashboard/", admin_dashboard, name='admindashbaord'),
    path("login/", Login, name="Login"),
    path("Profile/", profile_view, name="profile_view"),
    
    # AJAX endpoints - only working ones
    path('ajax/add_client/', add_client, name='add_client'),

 path('add-team-member/', addTeamMember, name='addTeamMember'),
 path('team-member-list/', teamMemberList, name='team_member_list'),
    path('delete-team-member/<int:member_id>/', deleteTeamMember, name='delete_team_member'),
    path('debug-team-members/', debug_team_members, name='debug_team_members'),

    path('teamTarget/', teamTarget, name='teamTarget'),
    path('ajax/add_team_target/', add_team_target, name='add_team_target'),


    path('projectstatus/', projectstatus, name='projectstatus'),
    path('ajax/update_project_status/', csrf_exempt(update_project_status), name='update_project_status'),
    path('ajax/view_project_details/', csrf_exempt(view_project_details), name='view_project_details'),
    path('export-project-status/', export_project_status, name='export_project_status'),


    path('client-transfer/', transferClient, name='client_transfer'),
    path('ajax/execute_client_transfer/', csrf_exempt(executeClientTransfer), name='execute_client_transfer'),
    path('ajax/get_clients_by_agent/', getClientsByAgent, name='get_clients_by_agent'),
    path('ajax/get_transferred_clients/', getTransferredClients, name='get_transferred_clients'),
    path('ajax/reverse_client_transfer/', csrf_exempt(reverseClientTransfer), name='reverse_client_transfer'),
]