# Generated by Django 3.2.15 on 2022-12-08 17:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eawork', '0032_rename_yearfounded_company_year_founded'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='external_links',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='company',
            name='internal_links',
            field=models.TextField(blank=True),
        ),
    ]
