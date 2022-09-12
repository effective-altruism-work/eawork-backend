from django.db import migrations


def set_is_refetch_from_80_000_hours(apps, schema_editor):
    JobPost = apps.get_model("eawork", "JobPost")
    JobPost.objects.all().update(is_refetch_from_80_000_hours=True)


class Migration(migrations.Migration):

    dependencies = [
        ("eawork", "0018_add_field_job_alert_last_checked_at"),
    ]

    operations = [
        migrations.RunPython(set_is_refetch_from_80_000_hours, migrations.RunPython.noop),
    ]
