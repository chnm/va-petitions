import json

from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from .models import County, Petition, Subject

THEME_LABELS = dict(Petition.THEME_CHOICES)
PER_PAGE = 50


def catalog(request):
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

    return render(request, 'petitions/catalog.html', {
        'nav_active': 'catalog',
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
    # Mappable counties (have coordinates and at least one petition). Their
    # order defines the index used by the client-side dataset below.
    counties = County.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False,
    ).annotate(
        total=Count('petitions')
    ).filter(total__gt=0).order_by('name')

    county_list = [{
        'name': c.name,
        'slug': c.slug,
        'lat': c.latitude,
        'lng': c.longitude,
    } for c in counties]
    county_index = {c.slug: i for i, c in enumerate(counties)}

    # Subjects for the dropdown, with overall counts (like the catalog).
    subjects = Subject.objects.annotate(
        c=Count('petitions')
    ).filter(c__gt=0).order_by('name')
    subject_list = [{'slug': s.slug, 'name': s.name, 'count': s.c} for s in subjects]
    subject_index = {s.slug: i for i, s in enumerate(subjects)}

    # Compact per-petition dataset: year + indices into the county/subject
    # arrays. The browser recomputes county counts from this as filters change.
    petitions = Petition.objects.prefetch_related('counties', 'subjects').all()
    petition_data = []
    for p in petitions:
        petition_data.append({
            'y': p.date.year if p.date else None,
            'c': [county_index[c.slug] for c in p.counties.all() if c.slug in county_index],
            's': [subject_index[s.slug] for s in p.subjects.all() if s.slug in subject_index],
        })

    years = [d['y'] for d in petition_data if d['y'] is not None]
    year_min = min(years) if years else 1773
    year_max = max(years) if years else 1861

    return render(request, 'petitions/map.html', {
        'nav_active': 'map',
        'counties_json': json.dumps(county_list),
        'subjects_json': json.dumps(subject_list),
        'petitions_json': json.dumps(petition_data),
        'subjects': subject_list,
        'total_petitions': len(petition_data),
        'year_min': year_min,
        'year_max': year_max,
    })


def map_county_detail(request, slug):
    """AJAX endpoint returning a county's petitions, honoring active filters."""
    county = get_object_or_404(County, slug=slug)
    petitions = county.petitions.all()

    subject = request.GET.get('subject')
    if subject:
        petitions = petitions.filter(subjects__slug=subject)

    def _year(param):
        value = request.GET.get(param)
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    year_from, year_to = _year('from'), _year('to')
    if year_from is not None:
        petitions = petitions.filter(date__year__gte=year_from)
    if year_to is not None:
        petitions = petitions.filter(date__year__lte=year_to)

    petitions = petitions.order_by('date').distinct()
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
