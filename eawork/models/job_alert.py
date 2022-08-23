from secrets import token_hex

from django.contrib.postgres.fields import HStoreField
from django.db import models
from django.db.models import JSONField

from eawork.models import TimeStampedModel


class JobAlert(TimeStampedModel):
    email = models.EmailField(max_length=511)
    query = JSONField()
    query_raw = models.URLField(max_length=1023)
    jobs_seen = HStoreField()
    post_pk_seen_last = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    unsubscribe_token = models.CharField(default=token_hex, max_length=10240)
