from django.contrib import admin

from eawork.models import JobAlert


@admin.register(JobAlert)
class JobAlertAdmin(admin.ModelAdmin):
    list_display = [
        "email",
        "is_active",
        "last_checked_at",
        "created_at",
        "query_json",
        "query_string",
    ]
    list_filter = [
        "is_active",
        "created_at",
        "updated_at",
        "last_checked_at",
    ]
