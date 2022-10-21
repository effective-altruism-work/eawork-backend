from auditlog.registry import auditlog
from django.db import models
from eawork.models import JobAlert
from eawork.models.job_post import JobPost
from eawork.models.time_stamped import TimeStampedModel
from eawork.models.user import User


class Unsubscription(TimeStampedModel):
    too_many_emails = models.BooleanField()
    alerts = models.BooleanField()
    unexpected = models.BooleanField()
    irrelevant = models.BooleanField()
    other_reason = models.TextField(max_length=1000)
    job_alert = models.ForeignKey(JobAlert, on_delete=models.CASCADE)

    def __str__(self):
        return f"#{self.pk}"
