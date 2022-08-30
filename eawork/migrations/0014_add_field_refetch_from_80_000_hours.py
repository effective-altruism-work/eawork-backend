from django.db import migrations
from django.db import models


def add_tag_types(apps, schema_editor):
    JobPost = apps.get_model("eawork", "JobPost")
    JobPost.objects.exclude(id_external_80_000_hours="").update(
        is_refetch_from_80_000_hours=True
    )


class Migration(migrations.Migration):

    dependencies = [
        ("eawork", "0013_add_field_version_current"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobpost",
            name="is_refetch_from_80_000_hours",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(add_tag_types, migrations.RunPython.noop),
    ]
