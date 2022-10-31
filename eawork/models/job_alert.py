from secrets import token_hex
from django.utils.http import urlencode
import urllib.parse
from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog
from django.db import models
from django.db.models import JSONField
from django.utils import timezone

from eawork.models.time_stamped import TimeStampedModel


class JobAlert(TimeStampedModel):
    email = models.EmailField(max_length=511)
    query_json = JSONField(null=True, blank=True)
    query_string = models.CharField(max_length=4095, blank=True)  # legacy, to be deleted
    last_checked_at = models.DateTimeField(null=True, blank=True, default=timezone.now)
    post_pk_seen_last = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    unsubscribe_token = models.CharField(default=token_hex, max_length=10240)

    history = AuditlogHistoryField()

    def __str__(self):
        return self.email

    def generate_query_string(self) -> str:
        query_string = "?"

        if self.query_json is None:
            return query_string

        # keyword
        keyword_query = self.query_json["query"]
        if keyword_query:
            query_string = query_string + "query=" + keyword_query

        # facets
        for subarr in self.query_json["facetFilters"]:
            for i, key_val in enumerate(subarr):
                if ":" not in key_val:
                    print(f": not in {key_val} for {self.query_json}")
                    continue

                [key, val] = key_val.split(":")

                if query_string != "?":
                    query_string = query_string + "&"

                query_string = (
                    query_string
                    + "refinementList%5B"
                    + urllib.parse.quote(key)
                    + "%5D%5B"
                    + str(i)
                    + "%5D="
                    + urllib.parse.quote(val)
                )

        return query_string


auditlog.register(JobAlert)
