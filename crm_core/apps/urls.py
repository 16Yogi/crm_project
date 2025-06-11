from django.urls import path
from apps.views.components.anotherView import another_view
from apps.views.components.startingCalling import startcalls
from apps.views.components.MyClientProgresses import *
from apps.views.components.myClients import *
from apps.views.components.myTarget import *
from apps.views.components.teamClients import *
from apps.views.components.teamTarget import *
from apps.views.components.projectStatus import *

urlpatterns = [
    path('', startcalls, name='startcall'),
    path('another/', another_view, name='another'),
    path('myclientprogress/',myClientprogress,name='myclientprogress'),
    path('myclient/',myclient,name='myclient'),
    path('mytarget/',mytarget,name="mytarget"),
    path('projectstatus/',projectstatus,name="projectstatus"),
    path('teamClients/',teamClient,name="teamClient"),
    path("teamTarget/",teamTarget,name="teamTarget"),
]
