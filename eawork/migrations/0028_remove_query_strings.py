# Generated by Django 3.2.15 on 2022-11-14 16:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eawork', '0027_auto_20221108_1138'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='jobalert',
            name='query_string',
        ),
    ]
