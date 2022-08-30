from algoliasearch_django import raw_search
from django.conf import settings
from django.urls import reverse

from eawork.models import JobAlert
from eawork.models import JobPostVersion
from eawork.send_email import send_email


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
            "facetFilters": getattr(job_alert.query_json, "facetFilters", []),
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
            f"""
                <li><a href="{job['url_external']}">{job['title']} at {job['company_name']}</a></li>
            """
            for job in jobs_new
        ]
    )
    message_html = f"""
        <p><a href="{settings.FRONTEND_URL}/{job_alert.query_string}">Link to your search results</a>.</p>
        
        <p>New matched jobs:<p>
        
        <ul>{jobs_list}</ul>
        
        <p>
            <a href="{settings.BASE_URL}{url_unsubscribe}" color="#718096">Unsubscribe</a>
        </p>
        """

    send_email(
        subject="EA Work Jobs Alert",
        message_html=message_html,
        email_to=job_alert.email,
    )
