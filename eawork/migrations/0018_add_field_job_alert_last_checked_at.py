# Generated by Django 3.2.15 on 2022-09-12 00:12

import django.utils.timezone
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ("eawork", "0017_add_field_tags_location_80k"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="jobalert",
            name="jobs_seen",
        ),
        migrations.AddField(
            model_name="jobalert",
            name="last_checked_at",
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True),
        ),
    ]
