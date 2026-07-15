import html

from django.db import migrations


def decode_description_entities(apps, schema_editor):
    Petition = apps.get_model('petitions', 'Petition')
    changed = []

    for petition in Petition.objects.exclude(description='').iterator(
        chunk_size=500
    ):
        decoded = html.unescape(petition.description)
        if decoded != petition.description:
            petition.description = decoded
            changed.append(petition)

    if changed:
        Petition.objects.bulk_update(
            changed,
            ['description'],
            batch_size=500,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('petitions', '0003_alter_petition_primary_theme'),
    ]

    operations = [
        migrations.RunPython(
            decode_description_entities,
            migrations.RunPython.noop,
        ),
    ]
