from django.http import HttpResponse
from django.shortcuts import render
def myClientprogress(request):
    # return HttpResponse("My client Progresses")
    return render(request,"component/myClientProgresses.html")
