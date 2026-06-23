from django.db.models import Count
from django.shortcuts import render

from petitions.models import County, Petition, Subject


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
