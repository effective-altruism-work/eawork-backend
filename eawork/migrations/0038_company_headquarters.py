# Generated by Django 3.2.16 on 2023-01-23 18:17

from django.db import migrations, models
import django.db.models.deletion
import eawork.models.tag


class Migration(migrations.Migration):

    dependencies = [
        ('eawork', '0037_jobposttag_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='headquarters',
            field=models.ForeignKey(limit_choices_to={'types__type': eawork.models.tag.JobPostTagTypeEnum['LOCATION_80K']}, null=True, on_delete=django.db.models.deletion.SET_NULL, to='eawork.jobposttag'),
        ),
    ]