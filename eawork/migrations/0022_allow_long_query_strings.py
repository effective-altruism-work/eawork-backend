# Generated by Django 3.2.15 on 2022-10-24 14:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eawork', '0021_add_unsubscription_model'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobalert',
            name='query_string',
            field=models.CharField(blank=True, max_length=4095),
        ),
    ]
