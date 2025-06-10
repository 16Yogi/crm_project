from django.urls import path
from apps.views.components.anotherView import another_view
from apps.views.components.startingCalling import startcalls

urlpatterns = [
    path('', startcalls, name='startcall'),
    path('another/', another_view, name='another'),
]
