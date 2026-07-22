from django.db.models import Count
from django.shortcuts import render

from petitions.models import Petition, Subject

from .models import Essay, Resource, ResourcePage


def introduction(request):
    return render(request, 'pages/introduction.html', {
        'essay': Essay.objects.first(),
        'nav_active': 'introduction',
    })


def resources(request):
    return render(request, 'pages/resources.html', {
        'page': ResourcePage.objects.first(),
        'resources': Resource.objects.filter(is_published=True),
        'nav_active': 'resources',
    })


def home(request):
    locality_values = Petition.objects.order_by().values_list(
        'locality_raw', flat=True
    ).distinct()
    named_localities = {
        locality.strip()
        for value in locality_values
        for locality in value.split(';')
        if locality.strip() and locality.strip().lower() != 'unknown'
    }

    return render(request, 'pages/home.html', {
        'petition_count': Petition.objects.count(),
        'locality_count': len(named_localities),
        'subject_count': Subject.objects.annotate(
            pc=Count('petitions')
        ).filter(pc__gt=0).count(),
    })


def about(request):
    return render(request, 'pages/about.html', {
        'nav_active': 'about',
    })
