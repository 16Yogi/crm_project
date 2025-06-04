from django.shortcuts import render

def login(request):
    return render(request,'forms/login.html')

def registration(request):
    return render(request,'forms/registration.html')