from typing import Type

import requests
from django.core.management.base import BaseCommand
from enumfields import Enum

from eawork.models import JobPost
from eawork.models import JobPostTag
from eawork.models import JobPostTagType
from eawork.models import JobPostTagTypeEnum
from eawork.models import JobPostVersion
from eawork.models import PostJobTagStatus


class Command(BaseCommand):
    def handle(self, *args, **options):
        resp = requests.get(url="https://api.80000hours.org/job-board/vacancies")
        jobs_raw = resp.json()["data"]["vacancies"][:30]

        for job_raw in jobs_raw:
            if JobPost.objects.filter(id_external_80_000_hours=job_raw["id"]).exists():
                post_version = JobPostVersion.objects.get(
                    post__id_external_80_000_hours=job_raw["id"]
                )
                post_version.title = job_raw["Job title"]
                post_version.description = self._get_job_desc(job_raw)
                post_version.url_external = job_raw["Link"]
                post_version.save()
            else:
                post = JobPost.objects.create(
                    id_external_80_000_hours=job_raw["id"],
                    is_published=True,
                )
                post_version = JobPostVersion.objects.create(
                    title=job_raw["Job title"],
                    description=self._get_job_desc(job_raw),
                    url_external=job_raw["Link"],
                )

                post.version_current = post_version
                post.save()
                post_version.post = post
                post_version.save()

                for role_type in job_raw["Role types"]:
                    tag = get_or_create_tag(
                        tag_name=role_type, tag_type=JobPostTagTypeEnum.ROLE_TYPE
                    )
                    post_version.tags_role_type.add(tag)

                for cause_area in job_raw["Problem areas"]:
                    tag = get_or_create_tag(
                        tag_name=cause_area, tag_type=JobPostTagTypeEnum.CAUSE_AREA
                    )
                    post_version.tags_cause_area.add(tag)

    def _get_job_desc(self, job_raw: dict) -> str:
        desc: str = job_raw["Job description"]
        if desc.startswith('"'):
            desc = desc[1:]
        if desc.endswith(' [...]"'):
            desc = desc[:-7]
        if desc.endswith('"'):
            desc = desc[:-1]
        return desc


def get_or_create_tag(tag_name: str, tag_type: Type[Enum]) -> JobPostTag:
    tag = JobPostTag.objects.filter(name__iexact=tag_name).first()
    if not tag:
        tag = JobPostTag.objects.create(
            name=tag_name,
            status=PostJobTagStatus.APPROVED,
        )
    tag_type = JobPostTagType.objects.get(type=tag_type)
    tag.types.add(tag_type)
    tag.save()
    return tag
