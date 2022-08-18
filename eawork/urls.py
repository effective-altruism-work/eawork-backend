from django.conf import settings
from django.contrib import admin
from django.urls import include
from django.urls import path

from eawork.settings import DjangoEnv


urlpatterns = [
    path("admin/", admin.site.urls),
    path("select2/", include("django_select2.urls")),
]

if settings.DJANGO_ENV in (DjangoEnv.LOCAL, DjangoEnv.DOCKER_BUILDER):
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
