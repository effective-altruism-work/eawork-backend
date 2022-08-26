import datetime
from typing import Any
from typing import Optional

from algoliasearch_django import save_record
from algoliasearch_django import update_records
from algoliasearch_django.decorators import disable_auto_indexing
from ninja import NinjaAPI
from ninja import Schema
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from eawork.api.serializers import JobPostVersionSerializer
from eawork.models import Company
from eawork.models import JobAlert
from eawork.models import JobPost
from eawork.models import JobPostTag
from eawork.models import JobPostTagType
from eawork.models import JobPostTagTypeEnum
from eawork.models import JobPostVersion
from eawork.models import PostJobTagStatus
from eawork.models import PostStatus
from eawork.models import User
from eawork.services.job_alert import check_new_jobs


class JobPostVersionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    queryset = JobPostVersion.objects.all()
    serializer_class = JobPostVersionSerializer


api_ninja = NinjaAPI(urls_namespace="api_ninja")


@api_ninja.get("/jobs/unsubscribe/{token}", url_name="jobs_unsubscribe")
def jobs_unsubscribe(request, token: str):
    alert = JobAlert.objects.filter(unsubscribe_token=token).last()
    if alert:
        alert.is_active = False
        alert.save()
        return "success"
    else:
        return "subscription doesn't exist"


class JobAlertReq(Schema):
    email: str
    query_json: Optional[Any]
    query_string: Optional[str]


@api_ninja.post("/jobs/subscribe", url_name="jobs_subscribe")
def jobs_subscribe(request, job_alert_req: JobAlertReq):
    job_alert = JobAlert.objects.create(
        email=job_alert_req.email,
        query_json=job_alert_req.query_json,
        query_string=job_alert_req.query_string,
    )
    check_new_jobs(job_alert, is_send_alert=False, algolia_hits_per_page=1)
    return {"success": True}


class JobPostJson(Schema):
    job_post_pk: str | int | None

    email: str
    company_name: str
    company_logo_url: str | None

    title: str
    description_short: str
    description: str | None
    url_external: str

    tags_generic: list[str] | None
    tags_area: list[str] | None
    tags_degree_required: list[str] | None
    tags_country: list[str] | None
    tags_city: list[str] | None
    tags_role_type: list[str] | None
    tags_location_type: list[str] | None
    tags_workload: list[str] | None
    tags_skill: list[str] | None
    tags_immigration: list[str] | None


@api_ninja.post("/jobs/create", url_name="jobs_create")
def jobs_create(request, job_post_json: JobPostJson):
    user = User.objects.filter(email=job_post_json.email).first()
    if not user:
        user = User.objects.create(email=job_post_json.email)

    if job_post_json.job_post_pk:
        job_post = JobPost.objects.get(pk=job_post_json.job_post_pk)

        _create_post_version(job_post, job_post_json, author=user)
    else:
        if job_post_json.company_name:
            company = Company.objects.filter(name=job_post_json.company_name).first()
        else:
            company = Company.objects.create(
                name=job_post_json.company_name,
                logo_url=job_post_json.company_logo_url,
                author=user,
            )

        job_post = JobPost.objects.create(
            author=user,
            company=company,
        )
        _create_post_version(job_post, job_post_json, author=user)

    return {"success": True}


def _create_post_version(job_post: JobPost, job_post_json: JobPostJson, author: User):
    with disable_auto_indexing():
        post_version = JobPostVersion.objects.create(
            post=job_post,
            author=author,
            status=PostStatus.NEEDS_REVIEW,
            title=job_post_json.title,
            description_short=job_post_json.description_short,
            description=job_post_json.description,
            url_external=job_post_json.url_external,
            posted_at=datetime.datetime.now(),
        )
        job_post_tags_pks = _add_tags(post_version, job_post_json, author)

    save_record(post_version)
    update_records(model=JobPostTag, qs=JobPost.objects.filter(pk__in=job_post_tags_pks))


def _add_tags(post_version: JobPostVersion, job_post_json: JobPostJson, author: User) -> list[int]:
    job_post_tags_pks: list[int] = []
    for enum_member in JobPostTagTypeEnum:
        tag_field_name = f"tags_{enum_member.value}"
        tag_names: list[str] = getattr(job_post_json, tag_field_name, [])
        for tag_name in tag_names or []:
            post_version_tag_field = getattr(post_version, tag_field_name)
            tag = _add_tag(post_version, tag_name=tag_name, tag_type=enum_member, author=author)
            post_version_tag_field.add(tag)
            job_post_tags_pks.append(tag.pk)
    return job_post_tags_pks


def _add_tag(
    post_version: JobPostVersion, tag_name: str, tag_type: JobPostTagTypeEnum, author: User
) -> JobPostTag:
    tag = JobPostTag.objects.filter(name__iexact=tag_name).first()
    if not tag:
        tag = JobPostTag.objects.create(
            name=tag_name,
            author=author,
            status=PostJobTagStatus.PENDING,
        )
        tag_type = JobPostTagType.objects.get(type=tag_type)
        tag.types.add(tag_type)
        tag.save()

    return tag
