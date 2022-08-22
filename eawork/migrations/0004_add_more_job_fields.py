# Generated by Django 3.2.15 on 2022-08-22 05:16

from django.db import migrations
from django.db import models

import eawork.models.job_post
from eawork.models import JobPostTagTypeEnum


def add_tag_types(apps, schema_editor):
    for tag_type in JobPostTagTypeEnum:
        JobPostTagType = apps.get_model("eawork", "JobPostTagType")
        JobPostTagType.objects.get_or_create(type=tag_type)


class Migration(migrations.Migration):

    dependencies = [
        ("eawork", "0003_add_fields_for_jobs"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="jobpostversion",
            name="tags_affiliation",
        ),
        migrations.RemoveField(
            model_name="jobpostversion",
            name="tags_cause_area",
        ),
        migrations.RemoveField(
            model_name="jobpostversion",
            name="tags_exp_required",
        ),
        migrations.AddField(
            model_name="jobpostversion",
            name="experience_avg",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="jobpostversion",
            name="experience_min",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="jobpostversion",
            name="salary_max",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="jobpostversion",
            name="salary_min",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="jobpostversion",
            name="tags_area",
            field=models.ManyToManyField(
                blank=True,
                limit_choices_to={
                    "types__type": eawork.models.job_post.JobPostTagTypeEnum["AREA"]
                },
                related_name="tags_area",
                to="eawork.JobPostTag",
            ),
        ),
        migrations.AddField(
            model_name="jobpostversion",
            name="tags_immigration",
            field=models.ManyToManyField(
                blank=True,
                limit_choices_to={
                    "types__type": eawork.models.job_post.JobPostTagTypeEnum["IMMIGRATION"]
                },
                related_name="tags_immigration",
                to="eawork.JobPostTag",
            ),
        ),
        migrations.AddField(
            model_name="jobpostversion",
            name="tags_location_type",
            field=models.ManyToManyField(
                blank=True,
                limit_choices_to={
                    "types__type": eawork.models.job_post.JobPostTagTypeEnum["LOCATION_TYPE"]
                },
                related_name="tags_location_type",
                to="eawork.JobPostTag",
            ),
        ),
        migrations.AddField(
            model_name="jobpostversion",
            name="tags_skill",
            field=models.ManyToManyField(
                blank=True,
                limit_choices_to={
                    "types__type": eawork.models.job_post.JobPostTagTypeEnum["SKILL"]
                },
                related_name="tags_skill",
                to="eawork.JobPostTag",
            ),
        ),
        migrations.AddField(
            model_name="jobpostversion",
            name="tags_workload",
            field=models.ManyToManyField(
                blank=True,
                limit_choices_to={
                    "types__type": eawork.models.job_post.JobPostTagTypeEnum["WORKLOAD"]
                },
                related_name="tags_workload",
                to="eawork.JobPostTag",
            ),
        ),
        migrations.RunPython(add_tag_types, migrations.RunPython.noop),
    ]
