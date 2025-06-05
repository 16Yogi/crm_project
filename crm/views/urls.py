from django.urls import path 
from . import views 

urlpatterns = [
    # path('',views.header,name='header'),
    # path('',views.layout,name='layout'),
    path('',views.startcalling,name='startcalling'),
    path('login/',views.login,name='login'),
    path('registraion/',views.registration,name='registration'),
]
