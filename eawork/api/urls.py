from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from eawork.api.views import JobPostVersionViewSet
from eawork.api.views import api_ninja
from eawork.api.views import create_tag_view


api_router = DefaultRouter()
api_router.register(r"jobs", JobPostVersionViewSet)

urlpatterns_api = [
    path(
        "api/",
        include(
            [
                path("jobs/tags/create/", create_tag_view),
                path("jobs/unsubscribe/<token>/", create_tag_view, name="jobs_unsubscribe"),
            ]
            + api_router.urls
        ),
    ),
    path("api/", api_ninja.urls)
]
