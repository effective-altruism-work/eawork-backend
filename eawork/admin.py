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
from eawork.models import JobAlert
from eawork.models import JobPost
from eawork.models import JobPostTag
from eawork.models import JobPostTagType
from eawork.models import JobPostTagTypeEnum
from eawork.models import JobPostVersion
from eawork.models import User
from eawork.models.comment import Comment


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


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "url",
        "linkedin_url",
        "facebook_url",
    ]
    search_fields = [
        "name",
    ]


@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
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
    list_filter = [("version_current__status", EnumFieldListFilter)]


@admin.register(JobPostTag)
class JobPostTagAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "author",
        "description",
        "status",
        "created_at",
    ]
    filter_horizontal = ["types"]
    autocomplete_fields = [
        "author",
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


@admin.register(JobAlert)
class JobAlertAdmin(admin.ModelAdmin):
    list_display = [
        "email",
        "post_pk_seen_last",
        "is_active",
        "created_at",
        "updated_at",
        "query_string",
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
