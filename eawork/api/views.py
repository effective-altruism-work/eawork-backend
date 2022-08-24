from typing import Any
from typing import Optional

from ninja import NinjaAPI
from ninja import Schema
from rest_framework import mixins
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from eawork.api.serializers import JobPostVersionSerializer
from eawork.api.serializers import TagSerializer
from eawork.models import JobAlert
from eawork.models import JobPostTag
from eawork.models import JobPostTagType
from eawork.models import JobPostVersion
from eawork.models import PostJobTagStatus
from eawork.services.job_alert import check_new_jobs


class JobPostVersionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    queryset = JobPostVersion.objects.all()
    serializer_class = JobPostVersionSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_tag_view(request: Request) -> Response:
    tag_name = request.data["name"].strip()
    tag = JobPostTag.objects.filter(name__iexact=tag_name).first()
    if not tag:
        tag = JobPostTag.objects.create(
            name=tag_name,
            author=request.user,
            status=PostJobTagStatus.PENDING,
        )

    tag_type = JobPostTagType.objects.get(type=request.data["type"])
    tag.types.add(tag_type)
    tag.save()
    return Response(TagSerializer(tag).data)


api_ninja = NinjaAPI()


@api_ninja.get("/jobs/unsubscribe/{token}", url_name="jobs_unsubscribe")
def jobs_unsubscribe(request, token: str):
    alert = JobAlert.objects.filter(unsubscribe_token=token)
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


@api_ninja.post("/jobs/subscribe/", url_name="jobs_subscribe")
def jobs_subscribe(request, job_alert_req: JobAlertReq):
    job_alert = JobAlert.objects.create(
        email=job_alert_req.email,
        query_json=job_alert_req.query_json,
        query_string=job_alert_req.query_string,
    )
    check_new_jobs(job_alert, is_send_alert=False, algolia_hits_per_page=1)
    return {"success": True}
