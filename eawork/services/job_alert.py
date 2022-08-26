import inspect

from algoliasearch_django import raw_search
from django.conf import settings
from django.core.mail import EmailMessage
from django.urls import reverse

from eawork.models import JobAlert
from eawork.models import JobPostVersion


def check_new_jobs_for_all_alerts():
    if settings.IS_ENABLE_ALGOLIA:  # todo remove
        for job_alert in JobAlert.objects.filter(is_active=True):
            check_new_jobs(job_alert)


def check_new_jobs(
    job_alert: JobAlert, is_send_alert: bool = True, algolia_hits_per_page: int = 500
):
    filters = {}
    if job_alert.post_pk_seen_last:
        filters = {"filters": f"post_pk > {job_alert.post_pk_seen_last}"}

    res_json = raw_search(
        model=JobPostVersion,
        query=job_alert.query_json["query"],
        params={
            "facetFilters": job_alert.query_json["facetFilters"],
            "hitsPerPage": algolia_hits_per_page,
            **filters,
        },
    )

    if res_json["hits"]:
        jobs_new = []
        for hit in res_json["hits"]:
            jobs_new.append(hit)

        if is_send_alert:
            _send_email(job_alert, jobs_new)

        job_alert.post_pk_seen_last = res_json["hits"][0]["objectID"]
        job_alert.save()


def _send_email(job_alert: JobAlert, jobs_new: list[dict]):
    url_unsubscribe = reverse(
        "api_ninja:jobs_unsubscribe", kwargs={"token": job_alert.unsubscribe_token}
    )
    jobs_list = "\n".join(
        [
            f"- {job['title']} at {job['company_name']} - {job['url_external']}"
            for job in jobs_new
        ]
    )
    message = inspect.cleandoc(
        f"""
        Your search results: {settings.FRONTEND_URL}/{job_alert.query_string}
        
        New matched jobs:
        {jobs_list}
        
        Unsubscribe: {settings.BASE_URL}{url_unsubscribe}
        """
    )

    msg = EmailMessage(
        subject="EA Work Jobs Alert",
        body=message,
        headers={"List-Unsubscribe": url_unsubscribe},
        from_email="support@eawork.org",
        to=[job_alert.email],
    )
    msg.send()
