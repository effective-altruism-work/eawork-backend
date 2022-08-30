from typing import Literal

import pytz
import requests
from algoliasearch_django import reindex_all
from algoliasearch_django.decorators import disable_auto_indexing
from dateutil.parser import parse
from django.conf import settings

from eawork.models import Company
from eawork.models import JobPost
from eawork.models import JobPostTag
from eawork.models import JobPostTagType
from eawork.models import JobPostTagTypeEnum
from eawork.models import JobPostVersion
from eawork.models import PostJobTagStatus
from eawork.models import PostStatus


def import_80_000_hours_jobs(json_to_import: dict = None, limit: int = None, is_import_companies: bool = True):
    with disable_auto_indexing():
        if json_to_import:
            data_raw = json_to_import["data"]
        else:
            resp = requests.get(url="https://api.80000hours.org/job-board/vacancies")
            data_raw = resp.json()["data"]

        if is_import_companies:
            _import_companies(data_raw)
        _import_jobs(data_raw, limit=limit, is_import_companies=is_import_companies)

    if settings.IS_ENABLE_ALGOLIA:
        reindex_all(JobPostVersion)
        reindex_all(JobPostTag)


def _import_companies(data_raw: dict):
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

def _import_jobs(data_raw: dict, limit: int = None, is_import_companies: bool = True):
    jobs_raw: list[dict] = _strip_all_json_strings(data_raw["vacancies"])

    if limit:
        jobs_raw = jobs_raw[:limit]

    for job_raw in jobs_raw:
        job_existing = JobPost.objects.filter(
            id_external_80_000_hours=job_raw["id"],
            version_current__isnull=False,
        ).last()

        if job_existing and not job_existing.is_refetch_from_80_000_hours:
            continue

        if job_existing:
            post_version_last = (
                JobPostVersion.objects.filter(
                    post__id_external_80_000_hours=job_raw["id"],
                    status=PostStatus.PUBLISHED,
                )
                .order_by("created_at")
                .last()
            )
            _update_post_version(post_version_last, job_raw)
        else:
            post = JobPost.objects.create(
                id_external_80_000_hours=job_raw["id"],
            )
            post_version = JobPostVersion.objects.create(
                title=job_raw["Job title"],
                status=PostStatus.PUBLISHED,
                post=post,
            )
            post.version_current = post_version
            if is_import_companies:
                post.company = Company.objects.get(
                    id_external_80_000_hours=job_raw["Hiring organisation ID"],
                )
            post.save()
            _update_post_version(post_version, job_raw)


def _update_post_version(version: JobPostVersion, job_raw: dict):
    version.title = job_raw["Job title"]
    version.description_short = _get_job_desc(job_raw)
    version.url_external = job_raw["Link"]

    hardcoded_80_000h_stub = "2050-01-01"
    if job_raw["Closing date"] != hardcoded_80_000h_stub:
        version.closes_at = parse(job_raw["Closing date"]).replace(
            tzinfo=pytz.timezone("Europe/London")
        )
    version.posted_at = parse(job_raw["Date listed"]).replace(
        tzinfo=pytz.timezone("Europe/London")
    )

    exp_reqs: str = job_raw["Experience requirements"]
    if exp_reqs == "5+ years of experience":
        version.experience_min = 5
    elif exp_reqs == "0-2 years of experience":
        version.experience_min = 0
        version.experience_avg = 2
    elif exp_reqs == "3-4 years of experience":
        version.experience_min = 3
        version.experience_avg = 4

    version.post.company = Company.objects.get(
        id_external_80_000_hours=job_raw["Hiring organisation ID"]
    )
    version.post.save()
    version.save()

    _update_or_add_tags(version, job_raw)


def _get_job_desc(job_raw: dict) -> str:
    desc: str = job_raw["Job description"]
    if desc.startswith('"'):
        desc = desc[1:]
    if desc.endswith(' [...]"'):
        desc = desc[:-7]
    if desc.endswith('"'):
        desc = desc[:-1]
    return desc


def _update_or_add_tags(post_version: JobPostVersion, job_raw: dict):
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
            if "remote" in city.lower():
                add_tag(
                    post=post_version,
                    tag_name="Remote",
                    tag_type=JobPostTagTypeEnum.LOCATION_TYPE,
                )
            elif city != "Remote":
                add_tag(
                    post=post_version,
                    tag_name=city,
                    tag_type=JobPostTagTypeEnum.CITY,
                )
        for country in job_raw["Locations"]["countries"]:
            if "remote" in country.lower():
                add_tag(
                    post=post_version,
                    tag_name="Remote",
                    tag_type=JobPostTagTypeEnum.LOCATION_TYPE,
                )
            elif country != "Remote":
                add_tag(
                    post=post_version,
                    tag_name=country,
                    tag_type=JobPostTagTypeEnum.COUNTRY,
                )

    SWE_roles = [
        "Front End Developer",
        "Full Stack Developer",
        "Full-stack Developer",
        "PHP Developer",
        "Project Lead, Molecular Systems Engineering Software",
        "Data Systems Developer",
        "Senior Data Systems Developer",
        "Software Developer",
        "Software Engineer",
        "S-Process Developer",
        "Lead Developer, Global",
        "Senior Developer / Team Lead",
        "Web Developer",
        "Android Security Developer",
        "Software Security Research Engineer",
        "Cyber Operations Developer, Registration of Interest",
        "Front-End Developer",
    ]
    for SWE_role in SWE_roles:
        if SWE_role in job_raw["Job title"] or job_raw["Job title"] == "Developer":
            add_tag(
                post=post_version,
                tag_name="Software Engineering",
                tag_type=JobPostTagTypeEnum.ROLE_TYPE,
            )
            break


def _strip_all_json_strings(jobs_raw: list[dict]) -> list[dict]:
    for job_raw in jobs_raw:
        for key in job_raw:
            value = job_raw[key]
            if type(value) is str:
                job_raw[key] = value.strip()
    return jobs_raw


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