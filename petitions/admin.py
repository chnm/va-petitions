from django.contrib import admin

from .models import County, Petition, Subject


@admin.register(County)
class CountyAdmin(admin.ModelAdmin):
    list_display = ['name', 'state', 'petition_count']
    list_filter = ['state']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

    def petition_count(self, obj):
        return obj.petitions.count()


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'petition_count']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

    def petition_count(self, obj):
        return obj.petitions.count()


@admin.register(Petition)
class PetitionAdmin(admin.ModelAdmin):
    list_display = ['serial', 'title', 'petition_type', 'date', 'locality_raw']
    list_filter = ['petition_type', 'subjects']
    search_fields = ['title', 'description', 'serial']
    filter_horizontal = ['counties', 'subjects']
    readonly_fields = ['rosetta_url']
