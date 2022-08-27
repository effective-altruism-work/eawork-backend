from django.db import models
from enumfields import Enum
from enumfields import EnumField

from eawork.models.time_stamped import TimeStampedModel
from eawork.models.user import User


class PostStatus(Enum):
    NEEDS_REVIEW = "needs_review"
    PUBLISHED = "published"

    HIDDEN = "hidden"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Post(TimeStampedModel):
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    # version_current = models.ForeignKey(
    #     PostVersion,
    #     blank=True,
    #     null=True,
    #     on_delete=models.SET_NULL,
    # )

    class Meta:
        abstract = True


class PostVersion(TimeStampedModel):
    # post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="versions")

    title = models.CharField(max_length=511)
    description_short = models.TextField(blank=True)
    description = models.TextField(blank=True)

    status = EnumField(PostStatus, default=PostStatus.PUBLISHED, max_length=255)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.title} | #{self.pk}"
