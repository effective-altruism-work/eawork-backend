from celery import shared_task, chain
from celery.utils.log import get_task_logger

import requests
from algoliasearch_django import reindex_all, raw_search
from algoliasearch_django.decorators import disable_auto_indexing
from django.conf import settings
from eawork.apps.job_alerts.job_alert import check_new_jobs_for_all_alerts

from eawork.models import JobPostVersion, JobPostTag, Company
from eawork.services.email_log import Code, Task, email_log
from eawork.services.import_80_000_hours import import_companies, import_jobs, refine_tags
from eawork.services.airtable import import_from_airtable

logger = get_task_logger(__name__)


@shared_task
def add(x, y):
    logger.info(f"Adding {x} + {y}")
    return x + y


@shared_task
def import_80_000_hours_jobs(
    json_to_import: dict = None,
    limit: int = None,
    is_reindex: bool = True,
    is_companies_only: bool = False,
    is_jobs_only: bool = False,
):
    print("import 80K")
    data_raw = {}
    with disable_auto_indexing():
        if json_to_import:
            data_raw = json_to_import["data"]
        else:
            # resp = requests.get(url="https://api.80000hours.org/job-board/vacancies")
            # data_raw = resp.json()["data"]
            data_raw = import_from_airtable()["data"]
        if is_companies_only:
            import_companies(data_raw)
            
        elif is_jobs_only:
            import_jobs(data_raw, limit=limit)
        else:
            import_companies(data_raw)
            import_jobs(data_raw, limit=limit)

        refine_tags(data_raw["problem_area_tags"])
    if is_reindex and settings.IS_ENABLE_ALGOLIA:
        reindex_algolia()


@shared_task
def old_import_80_000_hours_jobs(
    json_to_import: dict = None,
    limit: int = None,
    is_reindex: bool = True,
    is_companies_only: bool = False,
    is_jobs_only: bool = False,
):
    print("import 80K")
    data_raw = {}
    with disable_auto_indexing():
        if json_to_import:
            data_raw = json_to_import["data"]
        else:
            resp = requests.get(url="https://api.80000hours.org/job-board/vacancies")
            data_raw = resp.json()["data"]
        if is_companies_only:
            import_companies(data_raw)
        elif is_jobs_only:
            import_jobs(data_raw, limit=limit)
        else:
            import_companies(data_raw)
            import_jobs(data_raw, limit=limit)

    if is_reindex and settings.IS_ENABLE_ALGOLIA:
        reindex_algolia()


# ALGOLIA
@shared_task
def reindex_algolia():
    count = JobPostVersion.objects.all().count()
    print("reindex algolia")

    reindex_all(JobPostVersion)
    reindex_all(JobPostTag)
    reindex_all(Company)

    res = raw_search(JobPostVersion)
    hits = res.get("nbHits")

    successRatio = hits / count
    # they usually won't line up due to closing dates, so only alert if there's a significant difference
    if successRatio < 0.9:
        email_log(
            Task.INDEX_PARITY_CHECK,
            Code.FAILURE,
            content=f"We have {count} job post version in the DB, but Algolia only indexed {hits}",
        )
    else:
        email_log(
            Task.INDEX_PARITY_CHECK,
            Code.SUCCESS,
            content=f"Algolia indexed {hits} and we have {count} job post versions in our DB.",
        )


@shared_task
def check_new_jobs_celery():
    check_new_jobs_for_all_alerts()


def import_and_check_new_jobs_for_all_alerts(limit: int = None):
    print("sending to celery")
    # 'si' below makes the call signature immutable, otherwise the function becomes frightened that the previous function is trying to pass it an argument.
    chain(import_80_000_hours_jobs.s(limit=limit), check_new_jobs_celery.si()).apply_async()
