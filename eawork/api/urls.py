from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from eawork.api.views import JobPostVersionViewSet
from eawork.api.views import api_ninja


api_router = DefaultRouter()
api_router.register(r"jobs", JobPostVersionViewSet)

urlpatterns_api = [
    path("api/", api_ninja.urls),
    path(
        "api/",
        include(api_router.urls),
    ),
]
