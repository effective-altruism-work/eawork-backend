from rest_framework.routers import DefaultRouter

from eawork.api.views import JobPostVersionViewSet


api_router = DefaultRouter()
api_router.register(r"jobs", JobPostVersionViewSet)
