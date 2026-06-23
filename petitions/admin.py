from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm

from .models import County, Petition, Subject
from .resources import PetitionResource


@admin.register(County)
class CountyAdmin(ModelAdmin):
    list_display = ['name', 'state', 'petition_count']
    list_filter = ['state']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

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
    readonly_fields = ['rosetta_url']
