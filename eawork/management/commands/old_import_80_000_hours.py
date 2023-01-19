from django.core.management.base import BaseCommand

from eawork.tasks import old_import_80_000_hours_jobs


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("limit", type=int, nargs="?", default=False)

    def handle(self, *args, **options):
        # does not use celery for now for sake of synchronicity with check_new_jobs_for_all_alerts command
        old_import_80_000_hours_jobs(limit=options["limit"])
