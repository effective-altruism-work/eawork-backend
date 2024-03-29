from typing import Literal, TypedDict, Mapping

import pytz
import requests
import re
import markdown
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
from eawork.models.job_alert import JobAlert
from eawork.services.email_log import Code, Task, email_log
from sentry_sdk import capture_exception, capture_message


class AirtableTag(TypedDict):
    name: str
    link: str


def import_companies(data_raw: dict):
    print("import companies")
    companies_dict: dict[str, dict] = data_raw["organisations"]
    # bonus_data = _derive_some_company_data(data_raw)
    for company_id in companies_dict:
        company_raw: dict[
            Literal["name", "description", "homepage", "logo", "career_page", "headquarters"],
            str,
        ] = companies_dict[company_id]
        if Company.objects.filter(id_external_80_000_hours=company_id).exists():
            company = Company.objects.get(id_external_80_000_hours=company_id)
            company.name = company_raw["name"]
            company.description = markdown.markdown(company_raw["description"])
            company.description_short = markdown.markdown(company_raw["single_line_description"])
            company.text_hover = markdown.markdown(company_raw["text_hover"])
            company.year_founded = company_raw["founded_year"]
            company.org_size = company_raw["org_size"]
            company.is_top_recommended_org = company_raw["recommended_org"]
            company.additional_commentary = markdown.markdown(
                company_raw["additional_commentary"]
            )

            company.url = company_raw["homepage"]
            company.logo_url = company_raw["logo"]
            company.career_page_url = company_raw["career_page"]
            company.glassdoor_url = company_raw["glassdoor_link"]
            company.forum_url = company_raw["forum_link"]

            company.internal_links = markdown.markdown(company_raw["internal_links"])
            company.external_links = markdown.markdown(company_raw["external_links"])
            company.social_media_links = markdown.markdown(company_raw["social_media_links"])

            company.save()
            _update_or_add_tags_orgs(company, company_raw)
            add_headquarters(company, company_raw["headquarters"])

        else:
            comp = Company.objects.create(
                name=company_raw["name"],
                id_external_80_000_hours=company_raw["name"],
                description=markdown.markdown(company_raw["description"]),
                url=company_raw["homepage"],
                logo_url=company_raw["logo"],
                career_page_url=company_raw["career_page"],
                is_top_recommended_org=company_raw["recommended_org"],
                forum_url=company_raw["forum_link"],
            )

            _update_or_add_tags_orgs(comp, company_raw)


def import_jobs(data_raw: dict, limit: int = None):
    print("import jobs")

    try:
        jobs_raw: list[dict] = _strip_all_json_strings(data_raw["vacancies"])

        _cleanup_removed_jobs(jobs_raw)

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
                salary = job_raw["Salary (display)"]
                if not salary or salary == "Not Found":
                    salary = ""

                post = JobPost.objects.create(
                    id_external_80_000_hours=job_raw["id"],
                    is_refetch_from_80_000_hours=True,
                )
                post_version = JobPostVersion.objects.create(
                    title=job_raw["Job title"],
                    status=PostStatus.PUBLISHED,
                    salary=salary,
                    visa_sponsorship=job_raw["visa"],
                    evergreen=job_raw["evergreen"],
                    post=post,
                )
                post.version_current = post_version
                post.company = Company.objects.get(
                    id_external_80_000_hours=job_raw["Hiring organisation ID"],
                )
                post.save()
                _update_post_version(post_version, job_raw)

        count = JobPostVersion.objects.all().count()
        email_log(Task.IMPORT, Code.SUCCESS, content=f"{count} jobs imported")
    except Exception as err:
        email_log(Task.IMPORT, Code.FAILURE, content=f"Error:\n{err}")
        capture_exception(err)


# this is not analogous to the above imports. This adds metadata to existing tags in the database.
# airtable's tag IDs are not the same as our DB's tag ideas, so we find them by name and supply them with  bonus data.
def refine_tags(tags_raw: Mapping[str, AirtableTag]):
    count = 0
    missing = 0
    for key in tags_raw:
        count += 1
        tag = JobPostTag.objects.filter(name__iexact=tags_raw[key]["name"]).first()
        if not tag:
            missing += 1
            continue
        tag.link = tags_raw[key]["link"]
        tag.save()


def _cleanup_removed_jobs(jobs_raw: list[dict]):
    jobs_new_ids: list[str] = list(map(lambda job: job["id"], jobs_raw))
    jobs_current_ids: list[str] = JobPost.objects.exclude(
        id_external_80_000_hours=""
    ).values_list(
        "id_external_80_000_hours",
        flat=True,
    )
    ids_to_drop = set(jobs_current_ids) - set(jobs_new_ids)
    JobPost.objects.filter(id_external_80_000_hours__in=ids_to_drop).delete()


def _update_post_version(version: JobPostVersion, job_raw: dict):
    version.title = job_raw["Job title"]
    version.description_short = _get_job_desc(job_raw)
    version.url_external = job_raw["Link"]

    salary = job_raw["Salary (display)"]
    if not salary or salary == "Not Found":
        salary = ""

    version.salary = salary
    version.visa_sponsorship = job_raw["visa"]
    version.evergreen = job_raw["evergreen"]

    hardcoded_80_000h_stub = "2050-01-01"
    if job_raw["Closing date"] != hardcoded_80_000h_stub:
        version.closes_at = parse(job_raw["Closing date"]).replace(
            tzinfo=pytz.timezone("Etc/GMT0")
        )
    version.posted_at = parse(job_raw["Date listed"]).replace(tzinfo=pytz.timezone("Etc/GMT0"))

    exp_min: str = (
        job_raw["MinimumExperienceLevel"][0]
        if isinstance(job_raw["MinimumExperienceLevel"], list)
        else ""
    )
    if exp_min == "Senior (10+ years experience)":
        version.experience_min = 10
    elif exp_min == "Mid (5-9 years experience)":
        version.experience_min = 5
        version.experience_avg = 9

    elif exp_min == "Entry-level":
        version.experience_min = 0
        version.experience_avg = 2
    elif exp_min == "Junior (1-4 years experience)":
        version.experience_min = 1
        version.experience_avg = 4

    version.post.company = Company.objects.get(
        id_external_80_000_hours=job_raw["Hiring organisation ID"]
    )
    version.post.save()
    version.save()

    _update_or_add_tags_posts(version, job_raw)


def _get_job_desc(job_raw: dict) -> str:
    desc: str = job_raw["Job description"]
    if desc.startswith('"'):
        desc = desc[1:]
    if desc.endswith(' [...]"'):
        desc = desc[:-7]
    if desc.endswith('"'):
        desc = desc[:-1]
    return markdown.markdown(desc)


def update(alert: JobAlert):
    json = alert.query_json
    print(json)


def _update_or_add_tags_orgs(org: Company, org_raw: dict):
    org.tags_areas.clear()
    org.tags_locations.clear()

    for area in org_raw["tags"]:
        add_tag_org(
            org=org,
            tag_name=area,
            tag_type=JobPostTagTypeEnum.AREA,
        )

    for location in org_raw["locations"]:
        add_tag_org(
            org=org,
            tag_name=location,
            tag_type=JobPostTagTypeEnum.LOCATION_80K,
        )

    if len(org_raw["region"]) and org_raw["region"][0] is not None:
        add_tag_org(
            org=org, tag_name=org_raw["region"][0], tag_type=JobPostTagTypeEnum.LOCATION_80K
        )


def _update_or_add_tags_posts(post_version: JobPostVersion, job_raw: dict):
    post_version.tags_generic.clear()
    post_version.tags_area.clear()
    post_version.tags_area_filter.clear()
    post_version.tags_degree_required.clear()
    post_version.tags_exp_required.clear()
    post_version.tags_country.clear()
    post_version.tags_city.clear()
    post_version.tags_role_type.clear()
    post_version.tags_location_type.clear()
    post_version.tags_location_80k.clear()
    post_version.tags_workload.clear()
    post_version.tags_skill.clear()
    post_version.tags_immigration.clear()

    for role_type in job_raw["Role types"]:
        add_tag_post(
            post=post_version,
            tag_name=role_type,
            tag_type=JobPostTagTypeEnum.ROLE_TYPE,
        )

    #  these guys might have !Link for tag as well?
    pattern = re.compile(r"\w+\. ")  # account for API oddity for now.
    for area in job_raw["Problem areas"]:
        regexed_area = pattern.sub("", area, 1)
        add_tag_post(
            post=post_version,
            tag_name=regexed_area,
            tag_type=JobPostTagTypeEnum.AREA,
            concat="_filter",
        )

    # todo these guys have !Link for tag!
    for area in job_raw["Problem area (tags)"]:
        regexed_area = pattern.sub("", area, 1)
        add_tag_post(
            post=post_version,
            tag_name=regexed_area,
            tag_type=JobPostTagTypeEnum.AREA,
        )

    if job_raw["Degree requirements"]:
        add_tag_post(
            post_version,
            tag_name=job_raw["Degree requirements"],
            tag_type=JobPostTagTypeEnum.DEGREE_REQUIRED,
        )

    exp_min: str = (
        job_raw["MinimumExperienceLevel"][0]
        if isinstance(job_raw["MinimumExperienceLevel"], list)
        else ""
    )

    if exp_min:
        add_tag_post(
            post_version,
            tag_name=exp_min,
            tag_type=JobPostTagTypeEnum.EXP_REQUIRED,
        )

    for region in job_raw["Region"]:
        if region is not None:
            # we are counting regions as countries
            add_tag_post(
                post=post_version,
                tag_name=region,
                tag_type=JobPostTagTypeEnum.COUNTRY,
            )

            add_tag_post(
                post=post_version,
                tag_name=region,
                tag_type=JobPostTagTypeEnum.LOCATION_80K,
            )

    if job_raw["Locations"]:
        for city in job_raw["Locations"]["citiesAndCountries"]:
            if city == "":
                continue

            if "remote" in city.lower():
                add_tag_post(
                    post=post_version,
                    tag_name="Remote",
                    tag_type=JobPostTagTypeEnum.LOCATION_TYPE,
                )
            elif city != "Remote":
                # patch while api-builder is fixed
                if city[-1] == ",":
                    add_tag_post(
                        post=post_version,
                        tag_name=city[:-1],
                        tag_type=JobPostTagTypeEnum.COUNTRY,
                    )
                elif city[0] != ",":  # patch conditional while api-builder is fixed
                    add_tag_post(
                        post=post_version,
                        tag_name=city,
                        tag_type=JobPostTagTypeEnum.CITY,
                    )
            add_tag_post(
                post=post_version,
                tag_name=city,
                tag_type=JobPostTagTypeEnum.LOCATION_80K,
            )

        for country in job_raw["Locations"]["countries"]:
            if country == "":
                continue

            if "remote" in country.lower():
                add_tag_post(
                    post=post_version,
                    tag_name="Remote",
                    tag_type=JobPostTagTypeEnum.LOCATION_TYPE,
                )

            elif country == "Global":
                add_tag_post(
                    post=post_version,
                    tag_name="Remote, Global",
                    tag_type=JobPostTagTypeEnum.COUNTRY,
                )

            elif country != "Remote":
                add_tag_post(
                    post=post_version,
                    tag_name=country,
                    tag_type=JobPostTagTypeEnum.COUNTRY,
                )

            add_tag_post(
                post=post_version,
                tag_name=country,
                tag_type=JobPostTagTypeEnum.LOCATION_80K,
            )


def _strip_all_json_strings(jobs_raw: list[dict]) -> list[dict]:
    for job_raw in jobs_raw:
        for key in job_raw:
            value = job_raw[key]
            if type(value) is str:
                job_raw[key] = value.strip()
    return jobs_raw


def add_tag_post(
    post: JobPostVersion,
    tag_name: str,
    tag_type: JobPostTagTypeEnum,
    concat="",
):
    tag = JobPostTag.objects.filter(name__iexact=tag_name).first()
    if not tag:
        tag = JobPostTag.objects.create(
            name=tag_name,
            status=PostJobTagStatus.APPROVED,
        )
    tag_type_instance = JobPostTagType.objects.get(type=tag_type)
    tag.types.add(tag_type_instance)
    tag.save()
    if len(concat):
        getattr(post, f"tags_{tag_type.value}" + concat).add(tag)
    else:
        getattr(post, f"tags_{tag_type.value}").add(tag)


# basically a duplicate for now
def add_tag_org(org: Company, tag_name: str, tag_type: JobPostTagTypeEnum):
    tag = JobPostTag.objects.filter(name__iexact=tag_name).first()
    if not tag:
        tag = JobPostTag.objects.create(
            name=tag_name,
            status=PostJobTagStatus.APPROVED,
        )
    tag_type_instance = JobPostTagType.objects.get(type=tag_type)
    tag.types.add(tag_type_instance)
    tag.save()

    if tag_type.value == "area":
        getattr(org, "tags_areas").add(tag)
    elif tag_type.value == "location_80k":
        getattr(org, "tags_locations").add(tag)


def add_headquarters(org: Company, hq_name: str):
    if len(hq_name) == 0:
        return
    hq = JobPostTag.objects.filter(name__iexact=hq_name).first()
    if not hq:
        hq = JobPostTag.objects.create(
            name=hq_name,
            status=PostJobTagStatus.APPROVED,
        )
    hq_type_instance = JobPostTagType.objects.get(type=JobPostTagTypeEnum.LOCATION_80K)
    hq.types.add(hq_type_instance)
    hq.save()

    org.headquarters = hq
    org.save()
