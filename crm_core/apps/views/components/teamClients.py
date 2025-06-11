from django.shortcuts import render
from django.http import HttpResponse

def teamClient(request):
    # return HttpResponse("Team cliets")
    return render(request,"component/teamClients.html")