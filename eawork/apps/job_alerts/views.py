from typing import Any
from typing import Optional
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.template import Context, Template
from django.conf import settings

from ninja import Schema

from eawork.api.views import api_ninja
from eawork.apps.job_alerts.job_alert import check_new_jobs, get_total_jobs, send_confirmation
from eawork.apps.job_alerts.newsletter import (
    get_newsletter_subscription_status,
    post_newsletter_subscribe,
)
from eawork.models import JobAlert, job_alert
from eawork.models import unsubscription
from eawork.models.unsubscription import Unsubscription
from .forms import UnsubscribeForm
from sentry_sdk import capture_exception, capture_message
from ninja.errors import HttpError


@api_ninja.post("/jobs/unsubscribe/thankyou/{token}", url_name="jobs_unsubscribe_thanks")
def jobs_unsubscribe_response(request: HttpRequest, token: str):
    too_many_emails = bool(request.POST.get("too_many_emails"))
    alerts = bool(request.POST.get("alerts"))
    irrelevant = bool(request.POST.get("irrelevant"))
    unexpected = bool(request.POST.get("unexpected"))
    other_reason = str(request.POST.get("other_reason"))

    alert = JobAlert.objects.filter(unsubscribe_token=token).last()

    if alert is not None:
        unsubscription = Unsubscription.objects.create(
            too_many_emails=too_many_emails,
            alerts=alerts,
            irrelevant=irrelevant,
            unexpected=unexpected,
            other_reason=other_reason,
            job_alert=alert,
        )

        unsubscription.save()
    else:
        msg = f"A user attempted to send an unsubscription message, but their token was not for a valid alert: {token}"
        if not settings.DEBUG:
            capture_message(msg)
        else:
            print(msg)

    return render(request, "subscription/thankyou.html")


@api_ninja.get("/jobs/unsubscribe/{token}", url_name="jobs_unsubscribe")
def jobs_unsubscribe(request, token: str):
    alert = JobAlert.objects.filter(unsubscribe_token=token).last()

    if alert:
        alert.is_active = False
        alert.save()
        return render(
            request,
            "subscription/unsubscribe.html",
            {"base_url": settings.BASE_URL, "token": token},
        )
    else:
        return render(
            request,
            "subscription/notoken.html",
            {"base_url": settings.BASE_URL, "token": token},
        )


class JobAlertReq(Schema):
    email: str
    query_json: Optional[Any]


@api_ninja.post("/jobs/subscribe", url_name="jobs_subscribe")
def jobs_subscribe(request, job_alert_req: JobAlertReq):
    job_alert = JobAlert.objects.create(
        email=job_alert_req.email,
        query_json=job_alert_req.query_json,
    )

    total = get_total_jobs()
    check_new_jobs(job_alert, total, is_send_alert=False)
    send_confirmation(email=job_alert_req.email, unsubscribe_token=job_alert.unsubscribe_token)
    return {"success": True}


class NewsletterReq(Schema):
    email: str


@api_ninja.post("/jobs/newsletter/subscribe", url_name="newsletter_subscribe")
def newsletter_subscribe(request, newsletter_req: NewsletterReq):
    status = get_newsletter_subscription_status(newsletter_req.email)
    return post_newsletter_subscribe(email=newsletter_req.email, status=status)
