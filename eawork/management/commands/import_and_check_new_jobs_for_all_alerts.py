from django.core.management.base import BaseCommand

from eawork.tasks import import_and_check_new_jobs_for_all_alerts

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("limit", type=int, nargs="?", default=False)

    def handle(self, *args, **options):
        import_and_check_new_jobs_for_all_alerts(limit=options["limit"])
