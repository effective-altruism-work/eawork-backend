# Generated by Django 3.2.15 on 2022-08-27 01:13

import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ("eawork", "0012_alter_field_job_alert_query_string"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobpost",
            name="version_current",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="eawork.jobpostversion",
            ),
        ),
    ]
