from algoliasearch_django import raw_search
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from eawork.models import JobAlert
from eawork.models import JobPostVersion
from eawork.send_email import send_email
from eawork.services.email_log import Code, Task, email_log


def check_new_jobs_for_all_alerts():
    if settings.IS_ENABLE_ALGOLIA:  # todo remove
        print("\ncheck new jobs for all alerts")
        nohits = 0
        successes = 0
        failures = 0

        job_alert_count = 0
        for job_alert in JobAlert.objects.filter(is_active=True):
            job_alert_count += 1
            sent = check_new_jobs(job_alert)
            if sent is not None:
                if sent == True:
                    successes += 1
                else:
                    failures += 1
            else:
                nohits += 1

        content = """\nJob alert count: {job_alert_count}
        Alerts without new emails to send: {nohits}
        Successful emails: {successes}
        Failed emails: {failures}"""
        print(content)

        code = Code.SUCCESS if (nohits > 0 and successes > 0) else Code.FAILURE
        status = "failure" if code == Code.SUCCESS else "success"
        email_log(Task.EMAIL_ALERT, status, code, content=content)


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

    sent = None

    if res_json["hits"]:
        jobs_new = []
        for hit in res_json["hits"]:
            jobs_new.append(hit)

        if is_send_alert:
            sent = _send_email(
                job_alert, jobs_new
            )  # sent is overwritten with a bool to indicate the success status of an email

        job_alert.last_checked_at = timezone.now()
        job_alert.save()

    return sent  # if sent was not overwritten, its value remains None, indicating that there was nothing to send.


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
