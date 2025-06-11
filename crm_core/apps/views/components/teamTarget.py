from django.http import HttpResponse
from django.shortcuts import render

def teamTarget(request):
    # return HttpResponse("Team target")
    return render(request,"component/teamTarget.html")