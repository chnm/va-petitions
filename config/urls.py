from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('petitions/', include('petitions.urls')),
    path('', include('pages.urls')),
]
