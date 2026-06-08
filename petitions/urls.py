from django.urls import path

from . import views

app_name = 'petitions'

urlpatterns = [
    path('', views.petition_list, name='petition_list'),
    path('map/', views.map_view, name='map'),
    path('counties/', views.county_list, name='county_list'),
    path('counties/<slug:slug>/', views.county_detail, name='county_detail'),
    path('<int:serial>/', views.petition_detail, name='petition_detail'),
]
