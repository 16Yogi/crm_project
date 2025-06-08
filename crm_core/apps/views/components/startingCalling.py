from django.http import HttpResponse
from django.shortcuts import render

def startcalls():
    return render('component/startcalling.html')