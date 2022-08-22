from typing import Literal

import requests
from algoliasearch_django.decorators import disable_auto_indexing
from dateutil.parser import parse
from django.core.management.base import BaseCommand

from eawork.models import Company
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
            data_raw = resp.json()["data"]

            self._import_companies(data_raw)
            self._import_jobs(data_raw, limit=options["limit"])

    def _import_companies(self, data_raw: dict):
        companies_dict: dict[str, dict] = data_raw["organisations"]
        for company_id in companies_dict:
            company_raw: dict[
                Literal["name", "description", "homepage", "logo", "career_page"], str
            ] = companies_dict[company_id]
            if Company.objects.filter(id_external_80_000_hours=company_id).exists():
                company = Company.objects.get(id_external_80_000_hours=company_id)
                company.name = company_raw["name"]
                company.description = company_raw["description"]
                company.url = company_raw["homepage"]
                company.logo_url = company_raw["logo"]
                company.career_page_url = company_raw["career_page"]
            else:
                Company.objects.create(
                    name=company_raw["name"],
                    id_external_80_000_hours=company_raw["name"],
                    description=company_raw["description"],
                    url=company_raw["homepage"],
                    logo_url=company_raw["logo"],
                    career_page_url=company_raw["career_page"],
                )

    def _import_jobs(self, data_raw, limit: int = None):
        jobs_raw = data_raw["vacancies"]
        if limit:
            jobs_raw = jobs_raw[:limit]

        for job_raw in jobs_raw:
            is_job_exists = JobPost.objects.filter(
                id_external_80_000_hours=job_raw["id"],
                version_current__isnull=False,
            ).exists()
            if is_job_exists:
                post_version = JobPostVersion.objects.get(
                    post__id_external_80_000_hours=job_raw["id"]
                )
                self._update_post_version(post_version, job_raw)
            else:
                post = JobPost.objects.create(
                    id_external_80_000_hours=job_raw["id"],
                    is_published=True,
                )
                post.company = Company.objects.get(
                    id_external_80_000_hours=job_raw["Hiring organisation ID"]
                )
                post_version = JobPostVersion.objects.create(title=job_raw["Job title"])

                post.version_current = post_version
                post.save()
                post_version.post = post
                post_version.save()

                self._update_post_version(post_version, job_raw)

    def _update_post_version(self, version: JobPostVersion, job_raw: dict):
        version.title = job_raw["Job title"]
        version.description = self._get_job_desc(job_raw)
        version.url_external = job_raw["Link"]

        hardcoded_80_000h_stub = "2050-01-01"
        if job_raw["Closing date"] != hardcoded_80_000h_stub:
            version.closes_at = parse(job_raw["Closing date"])
        version.posted_at = parse(job_raw["Date listed"])

        version.post.company = Company.objects.get(
            id_external_80_000_hours=job_raw["Hiring organisation ID"]
        )
        version.post.save()
        version.save()

        self._update_or_add_tags(version, job_raw)

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
                if country == "Remote":
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
