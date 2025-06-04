from django.contrib import admin
from django.urls import path,include
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    # path('',views.home,name='home'),
    path('',include('views.urls'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
