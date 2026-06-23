from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(request):
    """Liveness check polled by the Docker host to restart the site if down."""
    return JsonResponse({'status': 'ok', 'code': 200})


urlpatterns = [
    path('health/', health, name='health'),
    path('admin/', admin.site.urls),
    path('', include('petitions.urls')),
    path('', include('pages.urls')),
]
