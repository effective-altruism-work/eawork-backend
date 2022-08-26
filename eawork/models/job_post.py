import html2text
from django.db import models
from enumfields import Enum
from enumfields import EnumField

from eawork.models import Company
from eawork.models import User
from eawork.models.post import Post
from eawork.models.post import PostStatus
from eawork.models.post import PostVersion


class JobPost(Post):
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        related_name="jobs",
        null=True,
        blank=True,
    )

    id_external_80_000_hours = models.CharField(max_length=255, blank=True)


class JobPostTagTypeEnum(Enum):
    GENERIC = "generic"
    AREA = "area"
    DEGREE_REQUIRED = "degree_required"
    COUNTRY = "country"
    CITY = "city"
    ROLE_TYPE = "role_type"
    LOCATION_TYPE = "location_type"
    WORKLOAD = "workload"
    SKILL = "skill"
    IMMIGRATION = "immigration"


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

    def get_types_formatted(self) -> list[str]:
        return [type_instance.type.value for type_instance in self.types.all()]

    def count(self) -> int:
        # todo probably doesn't work
        count = 0
        for enum_member in JobPostTagTypeEnum:
            for version in (
                JobPostVersion.objects.filter(status=PostStatus.PUBLISHED)
                .order_by("created_at")
                .distinct("post", "created_at")
            ):
                count += getattr(version, f"tags_{enum_member.value}").count()
        return count

    def __str__(self) -> str:
        return self.name


class JobPostVersion(PostVersion):
    post = models.ForeignKey(
        JobPost,
        on_delete=models.CASCADE,
        related_name="versions",
        null=True,
        blank=True,
    )

    closes_at = models.DateTimeField(null=True, blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)

    url_external = models.URLField(blank=True, max_length=1023)

    experience_min = models.PositiveIntegerField(null=True, blank=True)
    experience_avg = models.PositiveIntegerField(null=True, blank=True)

    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)

    tags_generic = models.ManyToManyField(
        JobPostTag,
        limit_choices_to={"types__type": JobPostTagTypeEnum.GENERIC},
        blank=True,
        related_name="tags_generic",
    )
    tags_area = models.ManyToManyField(
        JobPostTag,
        limit_choices_to={"types__type": JobPostTagTypeEnum.AREA},
        blank=True,
        related_name="tags_area",
    )
    tags_degree_required = models.ManyToManyField(
        JobPostTag,
        limit_choices_to={"types__type": JobPostTagTypeEnum.DEGREE_REQUIRED},
        blank=True,
        related_name=f"tags_{JobPostTagTypeEnum.DEGREE_REQUIRED.value}",
    )
    tags_country = models.ManyToManyField(
        JobPostTag,
        limit_choices_to={"types__type": JobPostTagTypeEnum.COUNTRY},
        blank=True,
        related_name=f"tags_{JobPostTagTypeEnum.COUNTRY.value}",
    )
    tags_city = models.ManyToManyField(
        JobPostTag,
        limit_choices_to={"types__type": JobPostTagTypeEnum.CITY},
        blank=True,
        related_name=f"tags_{JobPostTagTypeEnum.CITY.value}",
    )
    tags_role_type = models.ManyToManyField(
        JobPostTag,
        limit_choices_to={"types__type": JobPostTagTypeEnum.ROLE_TYPE},
        blank=True,
        related_name=f"tags_{JobPostTagTypeEnum.ROLE_TYPE.value}",
    )
    tags_location_type = models.ManyToManyField(
        JobPostTag,
        limit_choices_to={"types__type": JobPostTagTypeEnum.LOCATION_TYPE},
        blank=True,
        related_name=f"tags_{JobPostTagTypeEnum.LOCATION_TYPE.value}",
    )
    tags_workload = models.ManyToManyField(
        JobPostTag,
        limit_choices_to={"types__type": JobPostTagTypeEnum.WORKLOAD},
        blank=True,
        related_name=f"tags_{JobPostTagTypeEnum.WORKLOAD.value}",
    )
    tags_skill = models.ManyToManyField(
        JobPostTag,
        limit_choices_to={"types__type": JobPostTagTypeEnum.SKILL},
        blank=True,
        related_name=f"tags_{JobPostTagTypeEnum.SKILL.value}",
    )
    tags_immigration = models.ManyToManyField(
        JobPostTag,
        limit_choices_to={"types__type": JobPostTagTypeEnum.IMMIGRATION},
        blank=True,
        related_name=f"tags_{JobPostTagTypeEnum.IMMIGRATION.value}",
    )

    @property
    def get_post_pk(self) -> int:
        return self.post.pk

    def get_tags_area_formatted(self) -> list[str]:
        return [tag.name for tag in self.tags_area.all()]

    def get_tags_generic_formatted(self) -> list[str]:
        return [tag.name for tag in self.tags_generic.all()]

    def get_tags_degree_required_formatted(self) -> list[str]:
        return [tag.name for tag in self.tags_degree_required.all()]

    def get_tags_country_formatted(self) -> list[str]:
        return [tag.name for tag in self.tags_country.all()]

    def get_tags_city_formatted(self) -> list[str]:
        return [tag.name for tag in self.tags_city.all()]

    def get_tags_role_type_formatted(self) -> list[str]:
        return [tag.name for tag in self.tags_role_type.all()]

    def get_tags_location_type_formatted(self) -> list[str]:
        return [tag.name for tag in self.tags_location_type.all()]

    def get_tags_workload_formatted(self) -> list[str]:
        return [tag.name for tag in self.tags_workload.all()]

    def get_tags_skill_formatted(self) -> list[str]:
        return [tag.name for tag in self.tags_skill.all()]

    def get_tags_immigration_formatted(self) -> list[str]:
        return [tag.name for tag in self.tags_immigration.all()]

    def get_company_name(self) -> str:
        return self.post.company.name

    def get_company_url(self) -> str:
        return self.post.company.url

    def get_company_logo_url(self) -> str:
        return self.post.company.logo_url

    def get_company_career_page_url(self) -> str:
        return self.post.company.career_page_url

    def get_company_description(self) -> str:
        return self.post.company.description

    def get_description(self) -> str:
        return html2text.html2text(self.description)

    def get_description_short(self) -> str:
        return html2text.html2text(self.description_short)

    def is_should_submit_to_algolia(self) -> bool:
        if self.post:
            version_last = (
                self.post.versions.filter(status=PostStatus.PUBLISHED)
                .order_by("created_at")
                .last()
            )
            if version_last:
                return version_last.pk == self.pk
            else:
                return False
        else:
            return False
