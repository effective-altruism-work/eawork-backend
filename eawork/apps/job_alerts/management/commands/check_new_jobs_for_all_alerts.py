from django.core.management.base import BaseCommand

from eawork.apps.job_alerts.job_alert import check_new_jobs_for_all_alerts


class Command(BaseCommand):
    def handle(self, *args, **options):
        check_new_jobs_for_all_alerts()
