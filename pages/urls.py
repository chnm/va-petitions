from django.urls import path

from . import views

app_name = 'pages'

urlpatterns = [
    path('', views.home, name='home'),
    path('introduction/', views.introduction, name='introduction'),
    path('resources/', views.resources, name='resources'),
    path('about/', views.about, name='about'),
]
