import time

from django.contrib import admin, messages
from geopy.geocoders import Nominatim
from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm

from .models import County, Petition, Subject
from .resources import PetitionResource

STATE_NAMES = {
    'VA': 'Virginia',
    'WV': 'West Virginia',
    'KY': 'Kentucky',
    'PA': 'Pennsylvania',
}


@admin.action(description='Geocode selected counties (fill lat/lng via Nominatim)')
def geocode_counties(modeladmin, request, queryset):
    geolocator = Nominatim(user_agent='va-petitions-admin')
    success, skipped, failed = 0, 0, 0
    for county in queryset:
        if county.latitude is not None and county.longitude is not None:
            skipped += 1
            continue
        state_name = STATE_NAMES.get(county.state, county.state)
        query = f"{county.name}, {state_name}, USA"
        try:
            location = geolocator.geocode(query)
            if location:
                county.latitude = location.latitude
                county.longitude = location.longitude
                county.save(update_fields=['latitude', 'longitude'])
                success += 1
            else:
                failed += 1
        except Exception:
            failed += 1
        time.sleep(1.1)  # Nominatim rate limit
    modeladmin.message_user(
        request,
        f'Geocoded {success}, skipped {skipped} (already have coords), {failed} failed.',
        messages.SUCCESS if not failed else messages.WARNING,
    )


@admin.register(County)
class CountyAdmin(ModelAdmin):
    list_display = ['name', 'state', 'latitude', 'longitude', 'petition_count']
    list_filter = ['state']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    actions = [geocode_counties]

    def petition_count(self, obj):
        return obj.petitions.count()


@admin.register(Subject)
class SubjectAdmin(ModelAdmin):
    list_display = ['name', 'petition_count']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

    def petition_count(self, obj):
        return obj.petitions.count()


@admin.register(Petition)
class PetitionAdmin(ModelAdmin, ImportExportModelAdmin):
    resource_classes = [PetitionResource]
    import_form_class = ImportForm
    export_form_class = ExportForm
    list_display = ['serial', 'title', 'petition_type', 'kind', 'primary_theme', 'date', 'locality_raw']
    list_filter = ['petition_type', 'kind', 'primary_theme', 'subjects']
    list_editable = ['kind', 'primary_theme']
    search_fields = ['title', 'description', 'serial']
    filter_horizontal = ['counties', 'subjects']
