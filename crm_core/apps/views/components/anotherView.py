from django.http import HttpResponse

def another_view(request):
    return HttpResponse("Another View Page")
