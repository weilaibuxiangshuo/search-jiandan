from django.conf.urls import url, include
from django.contrib import admin


urlpatterns = [
    # url(r'^admin/', admin.site.urls),
    url(r'^user/', include('apps.userapp.urls', namespace='userapp')),
    url(r'^major/', include('apps.major.urls', namespace='major')),
]
