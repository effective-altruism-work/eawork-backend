import requests
from algoliasearch_django.decorators import disable_auto_indexing
from django.core.management.base import BaseCommand

from eawork.models import JobPost
from eawork.models import JobPostTag
from eawork.models import JobPostTagType
from eawork.models import JobPostTagTypeEnum
from eawork.models import JobPostVersion
from eawork.models import PostJobTagStatus


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("limit", type=int, nargs="?", default=False)

    def handle(self, *args, **options):
        with disable_auto_indexing():
            resp = requests.get(url="https://api.80000hours.org/job-board/vacancies")
            jobs_raw = resp.json()["data"]["vacancies"]
            if options["limit"]:
                jobs_raw = jobs_raw[: options["limit"]]

            for job_raw in jobs_raw:
                if JobPost.objects.filter(
                    id_external_80_000_hours=job_raw["id"], version_current__isnull=False
                ).exists():
                    post_version = JobPostVersion.objects.get(
                        post__id_external_80_000_hours=job_raw["id"]
                    )
                    post_version.title = job_raw["Job title"]
                    post_version.description = self._get_job_desc(job_raw)
                    post_version.url_external = job_raw["Link"]
                    post_version.save()

                    self._update_or_add_tags(post_version, job_raw)
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

                    self._update_or_add_tags(post_version, job_raw)

    def _get_job_desc(self, job_raw: dict) -> str:
        desc: str = job_raw["Job description"]
        if desc.startswith('"'):
            desc = desc[1:]
        if desc.endswith(' [...]"'):
            desc = desc[:-7]
        if desc.endswith('"'):
            desc = desc[:-1]
        return desc

    def _update_or_add_tags(self, post_version: JobPostVersion, job_raw: dict):
        for role_type in job_raw["Role types"]:
            add_tag(
                post=post_version,
                tag_name=role_type,
                tag_type=JobPostTagTypeEnum.ROLE_TYPE,
            )

        for area in job_raw["Problem areas"]:
            add_tag(
                post=post_version,
                tag_name=area,
                tag_type=JobPostTagTypeEnum.AREA,
            )

        if job_raw["Degree requirements"]:
            add_tag(
                post_version,
                tag_name=job_raw["Degree requirements"],
                tag_type=JobPostTagTypeEnum.DEGREE_REQUIRED,
            )

        if job_raw["Locations"]:
            for city in job_raw["Locations"]["citiesAndCountries"]:
                if city == "Remote":
                    add_tag(
                        post=post_version,
                        tag_name="Remote",
                        tag_type=JobPostTagTypeEnum.LOCATION_TYPE,
                    )
                else:
                    add_tag(
                        post=post_version,
                        tag_name=city,
                        tag_type=JobPostTagTypeEnum.CITY,
                    )
            for country in job_raw["Locations"]["citiesAndCountries"]:
                if city == "Remote":
                    add_tag(
                        post=post_version,
                        tag_name="Remote",
                        tag_type=JobPostTagTypeEnum.LOCATION_TYPE,
                    )
                else:
                    add_tag(
                        post=post_version,
                        tag_name=country,
                        tag_type=JobPostTagTypeEnum.COUNTRY,
                    )


def add_tag(post: JobPostVersion, tag_name: str, tag_type: JobPostTagTypeEnum):
    tag = JobPostTag.objects.filter(name__iexact=tag_name).first()
    if not tag:
        tag = JobPostTag.objects.create(
            name=tag_name,
            status=PostJobTagStatus.APPROVED,
        )
    tag_type_instance = JobPostTagType.objects.get(type=tag_type)
    tag.types.add(tag_type_instance)
    tag.save()
    getattr(post, f"tags_{tag_type.value}").add(tag)
