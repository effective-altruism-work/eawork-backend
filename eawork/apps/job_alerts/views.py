from typing import Any
from typing import Optional

from ninja import Schema

from eawork.api.views import api_ninja
from eawork.apps.job_alerts.job_alert import check_new_jobs
from eawork.models import JobAlert


@api_ninja.get("/jobs/unsubscribe/{token}", url_name="jobs_unsubscribe")
def jobs_unsubscribe(request, token: str):
    alert = JobAlert.objects.filter(unsubscribe_token=token).last()
    if alert:
        alert.is_active = False
        alert.save()
        return "success"
    else:
        return "subscription doesn't exist"


class JobAlertReq(Schema):
    email: str
    query_json: Optional[Any]
    query_string: Optional[str]


@api_ninja.post("/jobs/subscribe", url_name="jobs_subscribe")
def jobs_subscribe(request, job_alert_req: JobAlertReq):
    job_alert = JobAlert.objects.create(
        email=job_alert_req.email,
        query_json=job_alert_req.query_json,
        query_string=job_alert_req.query_string,
    )
    check_new_jobs(job_alert, is_send_alert=False)
    return {"success": True}
