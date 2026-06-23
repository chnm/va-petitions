"""django-import-export resource for the Petition model.

Drives the admin Import button: edit-or-append keyed on ``Serial`` from the
LVA spreadsheet (.xlsx or .csv), with a dry-run preview before committing.
"""
from import_export import fields, resources, widgets

from . import lva
from .models import Petition


class _DateWidget(widgets.Widget):
    def clean(self, value, row=None, **kwargs):
        return lva.parse_date(value)

    def render(self, value, obj=None, **kwargs):
        return value.isoformat() if value else ''


class _TypeWidget(widgets.Widget):
    def clean(self, value, row=None, **kwargs):
        return lva.parse_type(value)

    def render(self, value, obj=None, **kwargs):
        return dict(Petition.PETITION_TYPES).get(value, value or '')


class _DescriptionWidget(widgets.Widget):
    def clean(self, value, row=None, **kwargs):
        return lva.clean_description(value)

    def render(self, value, obj=None, **kwargs):
        return value or ''


class PetitionResource(resources.ModelResource):
    serial = fields.Field(attribute='serial', column_name='Serial',
                          widget=widgets.IntegerWidget())
    mms_id = fields.Field(attribute='mms_id', column_name='MMS ID')
    rosetta_ie = fields.Field(attribute='rosetta_ie', column_name='Rosetta IE')
    title = fields.Field(attribute='title', column_name='Title')
    petition_type = fields.Field(attribute='petition_type', column_name='Type',
                                 widget=_TypeWidget())
    date = fields.Field(attribute='date', column_name='Creation Date',
                        widget=_DateWidget())
    description = fields.Field(attribute='description', column_name='Description',
                              widget=_DescriptionWidget())
    locality_raw = fields.Field(attribute='locality_raw', column_name='Locality')
    permalink = fields.Field(attribute='permalink', column_name='permalink')

    class Meta:
        model = Petition
        import_id_fields = ('serial',)
        fields = ('serial', 'mms_id', 'rosetta_ie', 'title', 'petition_type',
                  'date', 'description', 'locality_raw', 'permalink')
        # Re-process every matched row so county/subject edits from the sheet
        # apply even when no scalar field changed.
        skip_unchanged = False
        clean_model_instances = False

    def before_import(self, dataset, **kwargs):
        # Build the name lookups once per import, not per row.
        self._county_lookup, self._subject_lookup = lva.build_lookups()
        return super().before_import(dataset, **kwargs)

    def skip_row(self, instance, original, row, import_validation_errors=None):
        # Ignore blank trailing rows (no Serial) rather than erroring on them.
        if not str(row.get('Serial') or '').strip():
            return True
        return super().skip_row(
            instance, original, row,
            import_validation_errors=import_validation_errors,
        )

    def after_save_instance(self, instance, row, **kwargs):
        # No PK on a no-transaction dry-run (nothing persisted) — skip relations.
        if instance.pk is None:
            return
        lva.assign_relations(
            instance, row, self._county_lookup, self._subject_lookup,
            replace=True,
        )
