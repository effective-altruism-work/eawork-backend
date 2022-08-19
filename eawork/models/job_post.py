from django.db import models
from enumfields import Enum
from enumfields import EnumField

from eawork.models.post import Post
from eawork.models.post import PostVersion


class JobPost(Post):
    version_current = models.OneToOneField(
        "eawork.JobPostVersion",
        null=True,
        on_delete=models.SET_NULL,
        related_query_name="post_current",
    )


class JobPostTagTypeEnum(Enum):
    GENERIC = "generic"
    AFFILIATION = "affiliation"
    CAUSE_AREA = "cause_area"


class JobPostTagType(models.Model):
    type = EnumField(JobPostTagTypeEnum, max_length=128, unique=True)

    def __str__(self):
        return str(self.type)


class PostJobTagStatus(Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"


class JobPostTag(models.Model):
    name = models.CharField(max_length=128, unique=True)
    types = models.ManyToManyField(JobPostTagType)
    author = models.ForeignKey(
        "eawork.JobPostVersion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    description = models.TextField(blank=True)
    synonyms = models.CharField(blank=True, max_length=1024)
    status = EnumField(PostJobTagStatus, default=PostJobTagStatus.APPROVED, max_length=64)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_types_formatted(self) -> list[str]:
        return [type_instance.type.value for type_instance in self.types.all()]

    def count(self) -> int:
        count = 0
        for enum_member in JobPostTagTypeEnum:
            lookup_name = f"version_current__tags_{enum_member.value}__in"
            count += JobPost.objects.filter(
                **{lookup_name: [self.pk]},
            ).count()
        return count

    def __str__(self):
        return self.name


class JobPostVersion(PostVersion):
    post = models.ForeignKey(
        JobPost,
        on_delete=models.CASCADE,
        related_name="versions",
        null=True,
        blank=True,
    )

    tags_generic = models.ManyToManyField(
        JobPostTag,
        limit_choices_to={"types__type": JobPostTagTypeEnum.GENERIC},
        blank=True,
        related_name="tags_generic",
    )
    tags_affiliation = models.ManyToManyField(
        JobPostTag,
        limit_choices_to={"types__type": JobPostTagTypeEnum.AFFILIATION},
        blank=True,
        related_name="tags_affiliation",
    )
    tags_cause_area = models.ManyToManyField(
        JobPostTag,
        limit_choices_to={"types__type": JobPostTagTypeEnum.CAUSE_AREA},
        blank=True,
        related_name="tags_cause_area",
    )

    def get_tags_cause_area_formatted(self) -> list[str]:
        return [tag.name for tag in self.tags_cause_area.all()]

    def get_tags_generic_formatted(self) -> list[str]:
        return [tag.name for tag in self.tags_generic.all()]

    def get_tags_affiliation_formatted(self) -> list[str]:
        return [tag.name for tag in self.tags_affiliation.all()]
