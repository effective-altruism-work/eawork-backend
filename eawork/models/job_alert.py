from secrets import token_hex

from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog
from django.db import models
from django.db.models import JSONField
from django.utils import timezone

from eawork.models.time_stamped import TimeStampedModel


class JobAlert(TimeStampedModel):
    email = models.EmailField(max_length=511)
    query_json = JSONField(null=True, blank=True)
    query_string = models.CharField(max_length=1023, blank=True)
    last_checked_at = models.DateTimeField(null=True, blank=True, default=timezone.now)
    post_pk_seen_last = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    unsubscribe_token = models.CharField(default=token_hex, max_length=10240)

    history = AuditlogHistoryField()

    def __str__(self):
        return self.email


auditlog.register(JobAlert)
