from algoliasearch_django import raw_search
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from eawork.models import JobAlert
from eawork.models import JobPostVersion
from eawork.send_email import send_email


def check_new_jobs_for_all_alerts():
    if settings.IS_ENABLE_ALGOLIA:  # todo remove
        successes = 0
        failures = 0
        for job_alert in JobAlert.objects.filter(is_active=True):
            sent = check_new_jobs(job_alert)
            if (sent is not None):
                if (sent == True):
                    successes += 1
                else:
                    failures += 1
        print(f"Successful emails: {successes}, failed emails: {failures}")

def check_new_jobs(
    job_alert: JobAlert,
    is_send_alert: bool = True,
    algolia_hits_per_page: int = 500,
):
    res_json = raw_search(
        model=JobPostVersion,
        query=job_alert.query_json.get("query", "") if job_alert.query_json else "",
        params={
            "facetFilters": job_alert.query_json.get("facetFilters", [])
            if job_alert.query_json
            else [],
            "hitsPerPage": algolia_hits_per_page,
            "filters": f"posted_at > {job_alert.last_checked_at.timestamp()}",
        },
    )
    if res_json["hits"]:
        jobs_new = []
        for hit in res_json["hits"]:
            jobs_new.append(hit)

        sent = None
        if is_send_alert:
            sent = _send_email(job_alert, jobs_new)
            

        job_alert.last_checked_at = timezone.now()
        job_alert.save()
        return sent


def _send_email(job_alert: JobAlert, jobs_new: list[dict]):
    return send_email(
        subject="New Jobs Alert [Beta]",
        template_name="job_alerts/job_alert.html",
        template_context={
            "url_unsubscribe": reverse(
                "api_ninja:jobs_unsubscribe", kwargs={"token": job_alert.unsubscribe_token}
            ),
            "jobs_new": jobs_new,
            "job_alert": job_alert,
        },
        email_to=job_alert.email,
    )
