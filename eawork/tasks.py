import json
from celery import shared_task, chain
from celery.utils.log import get_task_logger

import requests
from algoliasearch_django import reindex_all, raw_search
from algoliasearch_django.decorators import disable_auto_indexing
from django.conf import settings
from eawork.apps.job_alerts.job_alert import check_new_jobs_for_all_alerts

from eawork.models import JobPostTag
from eawork.models import JobPostVersion
from eawork.services.email_log import Code, Task, email_log
from eawork.services.import_80_000_hours import import_companies, import_jobs

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
    print("\nimport 80K")
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
    print("\nreindex algolia")
    
    reindex_all(JobPostVersion)
    reindex_all(JobPostTag)

    res = raw_search(JobPostVersion)
    hits = res.get("nbHits")

    if count == hits:
        email_log(Task.INDEX_PARITY_CHECK, Code.SUCCESS, content=f"Algolia indexed {hits}, which is the amount we have in our DB")
    else:
        email_log(
            Task.INDEX_PARITY_CHECK,
            Code.FAILURE,
            content=f"We have {count} job post version in the DB, but Algolia only indexed {hits}",
        )


@shared_task
def check_new_jobs_celery():
    check_new_jobs_for_all_alerts()


def import_and_check_new_jobs_for_all_alerts(limit: int = None):
    print("sending to celery")
    # 'si' below makes the call signature immutable, otherwise the function becomes frightened that the previous function is trying to pass it an argument.
    chain(import_80_000_hours_jobs.s(limit=limit), check_new_jobs_celery.si()).apply_async()
