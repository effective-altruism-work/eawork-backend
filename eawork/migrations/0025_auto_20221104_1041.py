# Generated by Django 3.2.15 on 2022-11-04 10:41

from django.db import migrations


def airtable_tweaks(apps, schema_editor):

    Alert = apps.get_model("eawork", "JobAlert")

    for alert in Alert.objects.all():
        # if no query, move on
        if alert.query_json is None:
            alert.save()
            continue

        for i, sub_arr in enumerate(alert.query_json["facetFilters"]):

            if len(sub_arr) == 0 or "tags_area" not in sub_arr[0]:
                continue  # skip non tags_area

            # REPLACE
            newS = list(
                map(
                    lambda x: x
                    if x != "tags_area:Institutional decision-making"
                    else "tags_area:Forecasting",
                    sub_arr,
                )
            )

            # international security and coop
            newS = list(
                map(
                    lambda x: x
                    if x != "tags_area:International security & cooperation"
                    else "tags_area:Other policy-focused roles",
                    newS,
                )
            )

            # FILTER
            newS = [
                x
                for x in newS
                if x
                not in [
                    "tags_area:Other (top recommended)",
                    "tags_area:Global priorities research",
                ]
            ]

            alert.query_json["facetFilters"][i] = newS

        alert.save()

def reverse(apps, schema_editor):
    print(reversed)


class Migration(migrations.Migration):

    dependencies = [
        ("eawork", "0024_auto_20221027_1250"),
    ]

    operations = [
        migrations.RunPython(airtable_tweaks, reverse_code=reverse),
    ]
