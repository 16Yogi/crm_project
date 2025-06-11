from django.shortcuts import render
from django.http import HttpResponse

def projectstatus(request):
    # return HttpResponse("This is project status")
    return render(request,"component/projectStatus.html")