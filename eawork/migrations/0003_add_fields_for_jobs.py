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
        ("eawork", "0002_alter_field_post_to_nullable"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobpost",
            name="id_external_80_000_hours",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="jobpostversion",
            name="closes_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="jobpostversion",
            name="posted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="jobpostversion",
            name="tags_city",
            field=models.ManyToManyField(
                blank=True,
                limit_choices_to={
                    "types__type": eawork.models.job_post.JobPostTagTypeEnum["CITY"]
                },
                related_name="tags_city",
                to="eawork.JobPostTag",
            ),
        ),
        migrations.AddField(
            model_name="jobpostversion",
            name="tags_country",
            field=models.ManyToManyField(
                blank=True,
                limit_choices_to={
                    "types__type": eawork.models.job_post.JobPostTagTypeEnum["COUNTRY"]
                },
                related_name="tags_country",
                to="eawork.JobPostTag",
            ),
        ),
        migrations.AddField(
            model_name="jobpostversion",
            name="tags_degree_required",
            field=models.ManyToManyField(
                blank=True,
                limit_choices_to={
                    "types__type": eawork.models.job_post.JobPostTagTypeEnum["DEGREE_REQUIRED"]
                },
                related_name="tags_degree_required",
                to="eawork.JobPostTag",
            ),
        ),
        migrations.AddField(
            model_name="jobpostversion",
            name="tags_exp_required",
            field=models.ManyToManyField(
                blank=True,
                limit_choices_to={
                    "types__type": eawork.models.job_post.JobPostTagTypeEnum["EXP_REQUIRED"]
                },
                related_name="tags_exp_required",
                to="eawork.JobPostTag",
            ),
        ),
        migrations.AddField(
            model_name="jobpostversion",
            name="tags_role_type",
            field=models.ManyToManyField(
                blank=True,
                limit_choices_to={
                    "types__type": eawork.models.job_post.JobPostTagTypeEnum["ROLE_TYPE"]
                },
                related_name="tags_role_type",
                to="eawork.JobPostTag",
            ),
        ),
        migrations.AddField(
            model_name="jobpostversion",
            name="url_external",
            field=models.URLField(blank=True, max_length=1023),
        ),
        migrations.RunPython(add_tag_types, migrations.RunPython.noop),
    ]
