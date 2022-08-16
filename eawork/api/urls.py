from django.urls import path
from rest_framework.routers import DefaultRouter

from eawork.api.views import PostJobVersionViewSet, create_tag_view

app_name = "job_posts_api"

router = DefaultRouter()
router.register(r"jobs", PostJobVersionViewSet)


urlpatterns = [
    path("profiles/tags/create/", create_tag_view),
] + router.urls
