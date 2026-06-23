import json

from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from .models import County, Petition, Subject

THEME_LABELS = dict(Petition.THEME_CHOICES)
PER_PAGE = 50


def catalogue(request):
    qs = Petition.objects.all().prefetch_related('subjects')
    total_count = qs.count()

    # Filters
    petition_type = request.GET.get('type', '')
    subject_slug = request.GET.get('subject', '')
    locality = request.GET.get('loc', '')

    if petition_type:
        qs = qs.filter(petition_type=petition_type)
    if subject_slug:
        qs = qs.filter(subjects__slug=subject_slug)
    if locality:
        qs = qs.filter(locality_raw=locality)

    # Sorting
    sort = request.GET.get('sort', 'date')
    direction = request.GET.get('dir', 'asc')
    if sort == 'name':
        order = 'title' if direction == 'asc' else '-title'
    else:
        order = 'date' if direction == 'asc' else '-date'
    qs = qs.order_by(order, 'serial')

    # Facet counts (from unfiltered set)
    type_counts = dict(
        Petition.objects.values_list('petition_type').annotate(c=Count('id')).values_list('petition_type', 'c')
    )
    subjects_with_counts = Subject.objects.annotate(
        c=Count('petitions')
    ).filter(c__gt=0).order_by('name')
    localities = (
        Petition.objects.exclude(locality_raw='')
        .values('locality_raw')
        .annotate(c=Count('id'))
        .order_by('locality_raw')
    )

    # Paginate
    paginator = Paginator(qs.distinct(), PER_PAGE)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)

    # Build query string without page param for pagination links
    query_params = request.GET.copy()
    query_params.pop('page', None)
    query_string = query_params.urlencode()

    return render(request, 'petitions/catalogue.html', {
        'nav_active': 'catalogue',
        'page': page,
        'total_count': total_count,
        'filtered_count': paginator.count,
        'type_counts': type_counts,
        'subjects_with_counts': subjects_with_counts,
        'localities': localities,
        'current_type': petition_type,
        'current_subject': subject_slug,
        'current_loc': locality,
        'current_sort': sort,
        'current_dir': direction,
        'query_string': query_string,
    })


def map_view(request):
    counties = County.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False,
    ).annotate(
        count=Count('petitions')
    ).filter(count__gt=0).order_by('-count', 'name')

    county_list = []
    for c in counties:
        county_list.append({
            'name': c.name,
            'slug': c.slug,
            'lat': c.latitude,
            'lng': c.longitude,
            'count': c.count,
        })

    total_petitions = Petition.objects.count()

    return render(request, 'petitions/map.html', {
        'nav_active': 'map',
        'counties_json': json.dumps(county_list),
        'total_petitions': total_petitions,
    })


def map_county_detail(request, slug):
    """AJAX endpoint returning petitions for a given county."""
    county = get_object_or_404(County, slug=slug)
    petitions = county.petitions.order_by('date')
    data = [{
        'title': p.title,
        'year': p.date.year if p.date else None,
        'description': p.description,
        'permalink': p.permalink,
    } for p in petitions]
    return JsonResponse(data, safe=False)


def search_view(request):
    q = request.GET.get('q', '').strip()
    results = []
    if q:
        results = Petition.objects.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(locality_raw__icontains=q) |
            Q(subjects__name__icontains=q)
        ).distinct().prefetch_related('subjects').order_by('date')[:100]

    example_terms = ['manumission', 'pension', 'Henrico', 'divorce', 'bridge', 'militia']

    return render(request, 'petitions/search.html', {
        'nav_active': 'search',
        'q': q,
        'results': results,
        'example_terms': example_terms,
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
