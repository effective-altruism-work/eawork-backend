from django.core.management.base import BaseCommand

from eawork.services.import_80_000_hours import import_80_000_hours_jobs


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("limit", type=int, nargs="?", default=False)

    def handle(self, *args, **options):
        import_80_000_hours_jobs(limit=options["limit"])
