from django.db.models import Count
from django.shortcuts import get_object_or_404, render

from .models import County, Petition, Subject


def petition_list(request):
    petitions = Petition.objects.all()

    petition_type = request.GET.get('type')
    if petition_type:
        petitions = petitions.filter(petition_type=petition_type)

    subject_slug = request.GET.get('subject')
    if subject_slug:
        petitions = petitions.filter(subjects__slug=subject_slug)

    return render(request, 'petitions/petition_list.html', {
        'petitions': petitions,
        'subjects': Subject.objects.annotate(count=Count('petitions')).filter(count__gt=0),
        'current_type': petition_type,
        'current_subject': subject_slug,
    })


def petition_detail(request, serial):
    petition = get_object_or_404(Petition, serial=serial)
    return render(request, 'petitions/petition_detail.html', {
        'petition': petition,
    })


def county_list(request):
    counties = County.objects.annotate(
        petition_count=Count('petitions')
    ).filter(petition_count__gt=0)

    state = request.GET.get('state')
    if state:
        counties = counties.filter(state=state)

    return render(request, 'petitions/county_list.html', {
        'counties': counties,
        'current_state': state,
    })


def county_detail(request, slug):
    county = get_object_or_404(County, slug=slug)
    petitions = county.petitions.all()
    return render(request, 'petitions/county_detail.html', {
        'county': county,
        'petitions': petitions,
    })


def map_view(request):
    counties = County.objects.annotate(
        petition_count=Count('petitions')
    ).filter(
        petition_count__gt=0,
        latitude__isnull=False,
        longitude__isnull=False,
    )
    return render(request, 'petitions/map.html', {
        'counties': counties,
    })
