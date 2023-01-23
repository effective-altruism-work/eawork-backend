from algoliasearch_django import raw_search
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, datetime

from eawork.models import JobAlert
from eawork.models import JobPostVersion
from eawork.send_email import send_email
from eawork.services.email_log import Code, Task, email_log


def check_new_jobs_for_all_alerts():
    if settings.IS_ENABLE_ALGOLIA:  # todo remove
        print("check new jobs for all alerts")
        nohits = 0
        successes = 0
        failures = 0

        job_alert_count = 0

        total_jobs = get_total_jobs()
        for job_alert in JobAlert.objects.filter(is_active=True):
            job_alert_count += 1
            sent = check_new_jobs(job_alert, total_jobs)
            if sent is not None:
                if sent == True:
                    successes += 1
                else:
                    failures += 1
            else:
                nohits += 1

        content = f"Job alert count: {job_alert_count}\nAlerts without new emails to send: {nohits}\nSuccessful emails: {successes}\nFailed emails: {failures}"
        print(content)

        code = Code.SUCCESS if (nohits > 0 or successes > 0) else Code.FAILURE
        email_log(Task.EMAIL_ALERT, code, content=content)


# possible there is an
def get_total_jobs() -> int:
    res_json = raw_search(
        model=JobPostVersion,
        query="",
        params={
            "facetFilters": [],
            "hitsPerPage": 3000,
        },
    )
    return len(res_json["hits"])


def check_new_jobs(
    job_alert: JobAlert,
    total_jobs: int,
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

    sent = None

    if res_json["hits"]:
        jobs_new = []

        any_closing_soon = False
        for hit in res_json["hits"]:
            hit["closing_soon"] = False
            if "closes_at" in hit and type(hit["closes_at"]) == int:
                hit["closing_soon"] = ((timezone.now() + timedelta(7)).timestamp()) > hit[
                    "closes_at"
                ]

                any_closing_soon = True
            jobs_new.append(hit)

        if is_send_alert:
            sent = _send_email(
                job_alert, jobs_new, any_closing_soon, total_jobs
            )  # sent is overwritten with a bool to indicate the success status of an email

        job_alert.last_checked_at = timezone.now()
        job_alert.save()

    return sent  # if sent was not overwritten, its value remains None, indicating that there was nothing to send.


def _send_email(
    job_alert: JobAlert, jobs_new: list[dict], any_closing_soon: bool, total_count: int
):
    query_string = job_alert.generate_query_string()

    matched_count = len(jobs_new)

    return send_email(
        subject="New Jobs Alert",
        template_name="job_alerts/job_alert.html",
        template_context={
            "url_unsubscribe": reverse(
                "api_ninja:jobs_unsubscribe", kwargs={"token": job_alert.unsubscribe_token}
            ),
            "jobs_new": jobs_new,
            "query_string": query_string,
            "any_closing_soon": any_closing_soon,
            "matched_count": matched_count,
            "total_count": total_count,
        },
        email_to=[job_alert.email],
    )


def send_confirmation(email: str, unsubscribe_token: str):
    return send_email(
        subject="Job alerts from 80,000 Hours - Confirmation",
        template_name="job_alerts/confirmation.html",
        template_context={
            "url_unsubscribe": reverse(
                "api_ninja:jobs_unsubscribe", kwargs={"token": unsubscribe_token}
            ),
        },
        email_to=[email],
    )
