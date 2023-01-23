from enumfields import Enum
from enumfields import EnumField
from django.db import models
from eawork.models.user import User


class JobPostTagTypeEnum(Enum):
    GENERIC = "generic"
    AREA = "area"
    DEGREE_REQUIRED = "degree_required"
    COUNTRY = "country"
    CITY = "city"
    ROLE_TYPE = "role_type"
    LOCATION_TYPE = "location_type"
    LOCATION_80K = "location_80k"
    WORKLOAD = "workload"
    SKILL = "skill"
    IMMIGRATION = "immigration"
    EXP_REQUIRED = "exp_required"


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
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    description = models.TextField(blank=True)
    synonyms = models.CharField(blank=True, max_length=1024)
    status = EnumField(PostJobTagStatus, default=PostJobTagStatus.APPROVED, max_length=64)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.TextField(blank=True)
    

    def get_types_formatted(self) -> list[str]:
        return [type_instance.type.value for type_instance in self.types.all()]

    def count(self) -> int:
        from eawork.models.job_post import JobPost

        count = 0
        for enum_member in JobPostTagTypeEnum:
            lookup_name = f"version_current__tags_{enum_member.value}__in"
            count += JobPost.objects.filter(**{lookup_name: [self.pk]}).count()
        return count

    def __str__(self) -> str:
        return self.name
