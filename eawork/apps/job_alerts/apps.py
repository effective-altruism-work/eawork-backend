from django.apps import AppConfig


class JobAlertConfig(AppConfig):
    name = "eawork.apps.job_alerts"

    def ready(self):
        from eawork.apps.job_alerts.views import jobs_subscribe
        from eawork.apps.job_alerts.views import jobs_unsubscribe
