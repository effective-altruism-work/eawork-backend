from django.contrib import admin

from eawork.models import JobAlert
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin


class AlertResource(resources.ModelResource):
    keyword_only = fields.Field()
    filters_only = fields.Field()

    def dehydrate_keyword_only(self, alert) -> str:
        query_json = getattr(alert, "query_json", None)

        if query_json is None or "query" not in query_json:
            return ""

        return query_json["query"]

    def dehydrate_filters_only(self, alert):
        query_json = getattr(alert, "query_json", None)

        if query_json is None or "facetFilters" not in query_json:
            return ""

        return query_json["facetFilters"]

    class Meta:
        model = JobAlert
        exclude = ("unsubscribe_token")
        export_order = (
            "email",
            "id",
            "is_active",
            "keyword_only",
            "filters_only",
            "query_json",
            "last_checked_at",
            "post_pk_seen_last",
            "created_at",
            "updated_at",
        )


class JobAlertAdmin(ImportExportModelAdmin):
    resource_class = AlertResource

    list_display = [
        "email",
        "is_active",
        "last_checked_at",
        "created_at",
        "query_json",
    ]

    list_filter = [
        "is_active",
        "created_at",
        "updated_at",
        "last_checked_at",
    ]


admin.site.register(JobAlert, JobAlertAdmin)
