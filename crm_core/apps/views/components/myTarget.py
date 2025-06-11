from django.shortcuts import render
from django.http import HttpResponse

def mytarget(request):
    # return HttpResponse("this is my target")
    return render(request,"component/myTarget.html")