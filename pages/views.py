from django.db.models import Count
from django.shortcuts import render

from petitions.models import County, Petition, Subject

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
    return render(request, 'pages/home.html', {
        'petition_count': Petition.objects.count(),
        'county_count': County.objects.annotate(
            pc=Count('petitions')
        ).filter(pc__gt=0).count(),
        'subject_count': Subject.objects.annotate(
            pc=Count('petitions')
        ).filter(pc__gt=0).count(),
    })


def about(request):
    return render(request, 'pages/about.html')
