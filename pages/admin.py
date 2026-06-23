from django.contrib import admin

from .models import Essay, Resource, ResourcePage


@admin.register(Essay)
class EssayAdmin(admin.ModelAdmin):
    list_display = ("title", "author_name", "updated_at")
    fieldsets = (
        (None, {"fields": ("kicker", "title", "deck")}),
        ("Author", {"fields": ("author_name", "author_title", "author_bio")}),
        ("Body", {"fields": ("body",)}),
    )

    def has_add_permission(self, request):
        # Singleton: only one essay row.
        return not Essay.objects.exists()


@admin.register(ResourcePage)
class ResourcePageAdmin(admin.ModelAdmin):
    list_display = ("title", "updated_at")

    def has_add_permission(self, request):
        # Singleton: one header row for the Resources page.
        return not ResourcePage.objects.exists()


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "order", "is_published")
    list_editable = ("order", "is_published")
    list_filter = ("category", "is_published")
