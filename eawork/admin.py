from adminutils import options
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django_object_actions import DjangoObjectActions
from enumfields.admin import EnumFieldListFilter

from eawork.models import Company
from eawork.models import JobPost
from eawork.models import JobPostTag
from eawork.models import JobPostTagType
from eawork.models import JobPostTagTypeEnum
from eawork.models import JobPostVersion
from eawork.models import User
from eawork.models.comment import Comment
from eawork.models.unsubscription import Unsubscription
from eawork.tasks import (
    import_and_check_new_jobs_for_all_alerts,
    reindex_algolia,
    import_80_000_hours_jobs,
    old_import_80_000_hours_jobs,
)


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = [
        "email",
        "is_active",
        "is_staff",
        "date_joined",
        "last_login",
    ]
    search_fields = [
        "email",
        "first_name",
        "last_name",
    ]
    ordering = ["email"]
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "email",
                    "password",
                    "first_name",
                    "last_name",
                ]
            },
        ),
        (
            "Permissions",
            {
                "fields": [
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ],
            },
        ),
        (
            "Important dates",
            {
                "fields": [
                    "last_login",
                    "date_joined",
                ]
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ["wide"],
                "fields": ["email", "password1", "password2"],
            },
        ),
    )


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "url", "year_founded"]
    search_fields = [
        "name",
    ]


@admin.register(JobPost)
class JobPostAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = [
        "version_current",
        "company",
        "author",
        "created_at",
        "updated_at",
    ]
    autocomplete_fields = [
        "author",
        "company",
        "version_current",
    ]
    search_fields = [
        "pk",
        "company__name",
        "versions__title",
        "id_external_80_000_hours",
    ]
    list_filter = [
        ("version_current__status", EnumFieldListFilter),
        "is_refetch_from_80_000_hours",
    ]
    changelist_actions = [
        "run_80k_import_companies",
        "run_80k_import_jobs",
        "reindex_algolia",
        "import_and_reindex",
    ]

    @options(label="Run 80k companies import")
    def run_80k_import_companies(self, request, queryset) -> HttpResponse:
        import_80_000_hours_jobs.delay(is_reindex=False, is_companies_only=True)
        messages.success(request, "Companies importing, await email")
        return redirect(reverse("admin:eawork_jobpost_changelist"))

    @options(label="Run 80k jobs import")
    def run_80k_import_jobs(self, request, queryset) -> HttpResponse:
        import_80_000_hours_jobs.delay(is_reindex=False, is_jobs_only=True)
        messages.success(request, "Jobs importing, await email")
        return redirect(reverse("admin:eawork_jobpost_changelist"))

    @options(label="Reindex Algolia")
    def reindex_algolia(self, request, queryset) -> HttpResponse:
        reindex_algolia.delay()
        messages.success(request, "Reindexing Algolia, await email")
        return redirect(reverse("admin:eawork_jobpost_changelist"))

    @options(label="Combined Import & Reindex")
    def import_and_reindex(self, request, queryset) -> HttpResponse:
        import_80_000_hours_jobs.delay(is_reindex=True)
        messages.success(request, "Importing and reindexing, await email")
        return redirect(reverse("admin:eawork_jobpost_changelist"))


@admin.register(JobPostTag)
class JobPostTagAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "author",
        "description",
        "status",
        "is_featured",
        "created_at",
        "link",
    ]
    filter_horizontal = ["types"]
    autocomplete_fields = [
        "author",
    ]
    list_filter = [
        "types",
        "is_featured",
        "created_at",
    ]


@admin.register(JobPostVersion)
class JobPostVersionAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = [
        "title",
        "status",
        "created_at",
        "closes_at",
        "posted_at",
    ]
    autocomplete_fields = [
        "post",
    ]
    search_fields = [
        "title",
    ]
    filter_horizontal = [f"tags_{tag_type_enum.value}" for tag_type_enum in JobPostTagTypeEnum]
    list_filter = [("status", EnumFieldListFilter)] + [
        f"tags_{tag_type_enum.value}" for tag_type_enum in JobPostTagTypeEnum
    ]

    change_actions = [
        "publish",
    ]

    @options(label="Publish")
    def publish(self, request, obj: JobPostVersion) -> HttpResponse:
        obj.publish()
        messages.success(request, "Version published")
        return redirect(reverse("admin:eawork_jobpostversion_change", args=[obj.id]))


@admin.register(JobPostTagType)
class JobPostTagTypeAdmin(admin.ModelAdmin):
    list_display = [
        "type",
    ]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = [
        "author",
        "post",
        "parent",
        "get_content",
        "created_at",
    ]
    autocomplete_fields = [
        "author",
        "post",
        "parent",
    ]
    search_fields = [
        "author",
        "content",
    ]

    @options(desc="Content")
    def get_content(self, obj: JobPostVersion) -> str:
        return str(obj)


@admin.register(Unsubscription)
class UnsubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        "too_many_emails",
        "alerts",
        "unexpected",
        "irrelevant",
        "other_reason",
        "created_at",
        "job_alert",
        "get_query_json",
    ]

    def get_query_json(self, obj):
        return obj.job_alert.query_json

    get_query_json.short_description = "Query JSON"

    search_fields = ["other_reason"]
