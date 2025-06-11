from django.shortcuts import render
from django.http import HttpResponse
def myclient(request):
    # return HttpResponse("My client")
    return render(request,"component/myClients.html")