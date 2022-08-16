from rest_framework import mixins
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from eawork.api.serializers import PostJobVersionSerializer
from eawork.api.serializers import TagSerializer
from eawork.models import PostJobTag
from eawork.models import PostJobTagStatus
from eawork.models import PostJobTagType
from eawork.models import PostJobVersion


class PostJobVersionViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    queryset = PostJobVersion.objects.filter(user__is_active=True)
    serializer_class = PostJobVersionSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_tag_view(request: Request) -> Response:
    tag_name = request.data["name"].strip()
    tag = PostJobVersion.objects.filter(name__iexact=tag_name).first()
    if not tag:
        tag = PostJobTag.objects.create(
            name=tag_name,
            author=request.user,
            status=PostJobTagStatus.PENDING,
        )

    tag_type = PostJobTagType.objects.get(type=request.data["type"])
    tag.types.add(tag_type)
    tag.save()
    return Response(TagSerializer(tag).data)
