from django.contrib import admin

from eawork.models import Company
from eawork.models import JobAlert
from eawork.models import JobPost
from eawork.models import JobPostTag
from eawork.models import JobPostTagType
from eawork.models import JobPostTagTypeEnum
from eawork.models import JobPostVersion


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "linkedin_url",
        "facebook_url",
    ]


@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    list_display = [
        "version_current",
        "id_external_80_000_hours",
        "pk",
        "created_at",
        "updated_at",
        "author",
        "is_published",
    ]


@admin.register(JobPostTag)
class JobPostTagAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "author",
        "description",
        "status",
        "created_at",
    ]


@admin.register(JobPostVersion)
class JobPostVersionAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "pk",
        "created_at",
        "closes_at",
        "posted_at",
    ]
    filter_horizontal = [f"tags_{tag_type_enum.value}" for tag_type_enum in JobPostTagTypeEnum]
    list_filter = [f"tags_{tag_type_enum.value}" for tag_type_enum in JobPostTagTypeEnum]


@admin.register(JobPostTagType)
class JobPostTagTypeAdmin(admin.ModelAdmin):
    list_display = [
        "type",
    ]


@admin.register(JobAlert)
class JobPostTagTypeAdmin(admin.ModelAdmin):
    list_display = [
        "email",
        "query_string",
        "query_string",
        "post_pk_seen_last",
        "is_active",
    ]
