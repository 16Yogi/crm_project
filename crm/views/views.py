from django.shortcuts import render

def login(request):
    return render(request,'forms/login.html')

def registration(request):
    return render(request,'forms/registration.html')

def layout(request):
    return render(request,'layout.html')

# components
def startcalling(request):
    customers = []
    for i in range(1, 16):  
        customers.append({
            'id': i,
            'name': f'Customer {i}',
            'status': 'Active' if i % 2 == 0 else 'Inactive',
            'handle': f'@customer{i}',
            'action': 'hello',
        })
    return render(request, 'component/startcalling.html', {'customers': customers})

