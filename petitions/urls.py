from django.urls import path

from . import views

app_name = 'petitions'

urlpatterns = [
    path('catalogue/', views.catalogue, name='catalogue'),
    path('map/', views.map_view, name='map'),
    path('map/county/<slug:slug>/', views.map_county_detail, name='map_county_detail'),
    path('search/', views.search_view, name='search'),
    path('counties/', views.county_list, name='county_list'),
    path('counties/<slug:slug>/', views.county_detail, name='county_detail'),
    path('<int:serial>/', views.petition_detail, name='petition_detail'),
]
