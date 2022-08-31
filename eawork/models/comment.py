from auditlog.registry import auditlog
from django.db import models

from eawork.models.job_post import JobPost
from eawork.models.time_stamped import TimeStampedModel
from eawork.models.user import User


class Comment(TimeStampedModel):
    post = models.ForeignKey(JobPost, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    is_deleted = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.content[:55]


auditlog.register(Comment)
