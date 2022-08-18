from django.contrib import admin

from eawork.models import Company
from eawork.models import JobPost
from eawork.models import JobPostTag
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
    ]
