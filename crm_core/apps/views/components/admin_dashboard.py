from django.shortcuts import render


def admin_dashboard(request):
    return render(request,'component/admin_dashboard.html')