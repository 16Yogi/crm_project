from django.http import HttpResponse
from django.shortcuts import render

def startcalls(request):
    # return HttpResponse("Start Calling Page")
    return render(request,'component/startcalling.html')


