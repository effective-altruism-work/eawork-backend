# Generated by Django 3.2.15 on 2022-12-08 17:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eawork', '0031_auto_20221208_1734'),
    ]

    operations = [
        migrations.RenameField(
            model_name='company',
            old_name='yearFounded',
            new_name='year_founded',
        ),
    ]
