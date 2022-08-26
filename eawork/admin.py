from django.contrib import admin

from eawork.models import Company
from eawork.models import JobAlert
from eawork.models import JobPost
from eawork.models import JobPostTag
from eawork.models import JobPostTagType
from eawork.models import JobPostTagTypeEnum
from eawork.models import JobPostVersion
from eawork.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        "email",
        "is_active",
        "is_staff",
        "date_joined",
        "last_login",
    ]
    search_fields = [
        "email",
    ]


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
        "get_title",
        "id_external_80_000_hours",
        "company",
        "author",
        "created_at",
        "updated_at",
    ]
    autocomplete_fields = [
        "author",
        "company",
    ]
    search_fields = [
        "pk",
        "company__name",
        "versions__title",
        "id_external_80_000_hours",
    ]

    def get_title(self, obj: JobPost) -> str:
        return str(obj)


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
class JobPostVersionAdmin(admin.ModelAdmin):
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
    filter_horizontal = [f"tags_{tag_type_enum.value}" for tag_type_enum in JobPostTagTypeEnum]
    list_filter = ["status"] + [
        f"tags_{tag_type_enum.value}" for tag_type_enum in JobPostTagTypeEnum
    ]


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
