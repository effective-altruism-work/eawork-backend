from rest_framework import mixins
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from eawork.api.serializers import JobPostVersionSerializer
from eawork.api.serializers import TagSerializer
from eawork.models import JobPostTag
from eawork.models import JobPostTagType
from eawork.models import JobPostVersion
from eawork.models import PostJobTagStatus


class JobPostVersionViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    queryset = JobPostVersion.objects.filter(user__is_active=True)
    serializer_class = JobPostVersionSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_tag_view(request: Request) -> Response:
    tag_name = request.data["name"].strip()
    tag = JobPostVersion.objects.filter(name__iexact=tag_name).first()
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
