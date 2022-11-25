import html2text
from django.db import models
from django.utils import timezone
from eawork.models.tag import JobPostTag, JobPostTagTypeEnum, PostJobTagStatus

import logging

from eawork.models.company import Company
from eawork.models.post import Post
from eawork.models.post import PostStatus
from eawork.models.post import PostVersion


class JobPost(Post):
    version_current = models.ForeignKey(
        "eawork.JobPostVersion",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        related_name="jobs",
        null=True,
        blank=True,
    )
    id_external_80_000_hours = models.CharField(max_length=255, blank=True)
    is_refetch_from_80_000_hours = models.BooleanField(default=False)

    def __str__(self):
        if self.version_current:
            return f"{self.version_current.title} | #{self.pk}"
        else:
            return str(self.pk)


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

    salary = models.TextField(blank=True)

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
    tags_exp_required = models.ManyToManyField(
        JobPostTag,
        limit_choices_to={"types__type": JobPostTagTypeEnum.EXP_REQUIRED},
        blank=True,
        related_name=f"tags_{JobPostTagTypeEnum.EXP_REQUIRED.value}",
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
    tags_location_80k = models.ManyToManyField(
        JobPostTag,
        limit_choices_to={"types__type": JobPostTagTypeEnum.LOCATION_80K},
        blank=True,
        related_name=f"tags_{JobPostTagTypeEnum.LOCATION_80K.value}",
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

    def publish(self):
        self.post.version_current = self
        self.post.is_refetch_from_80_000_hours = False
        self.post.save()
        self.status = PostStatus.PUBLISHED
        self.save()

    @property
    def get_post_pk(self) -> int:
        return self.post.pk

    def get_tags_area_formatted(self) -> list[str]:
        return [tag.name for tag in self.tags_area.all()]

    def get_tags_generic_formatted(self) -> list[str]:
        return [tag.name for tag in self.tags_generic.all()]

    def get_tags_degree_required_formatted(self) -> list[str]:
        return [tag.name for tag in self.tags_degree_required.all()]

    def get_tags_exp_required_formatted(self) -> list[str]:
        return [tag.name for tag in self.tags_exp_required.all()]

    def get_tags_country_formatted(self) -> list[str]:
        return [tag.name for tag in self.tags_country.all()]

    def get_tags_city_formatted(self) -> list[str]:
        return [tag.name for tag in self.tags_city.all()]

    def get_tags_role_type_formatted(self) -> list[str]:
        return [tag.name for tag in self.tags_role_type.all()]

    def get_tags_location_80k_formatted(self) -> list[str]:
        return [tag.name for tag in self.tags_location_80k.all()]

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

    def get_company_ea_forum_url(self) -> str:
        return self.post.company.forum_url

    def get_company_is_top_recommended_org(self) -> bool:
        return self.post.company.is_top_recommended_org

    def get_company_description(self) -> str:
        return self.post.company.description

    def get_id_external_80_000_hours(self) -> str:
        return self.post.id_external_80_000_hours

    def get_description_for_search(self) -> str:
        return (
            html2text.html2text(self.description_short)
            + "\n"
            + html2text.html2text(self.description)
        )

    def get_combined_org_data(self) -> list[str]:
        name = self.get_company_name()
        arr = [name]
        if self.get_company_is_top_recommended_org():
            arr.append("is_recommended_org")
        return arr

    def is_should_submit_to_algolia(self) -> bool:
        if self.post:
            is_active = True
            if self.closes_at:
                is_active = timezone.now() <= self.closes_at

            if not self.post.version_current:
                str = f"Post {self.post.pk} has no version_current field. Please check Post {self.post.pk} and PostVersion {self.pk}."
                print(str)
                logging.error(str)
                return False

            factors = (
                is_active
                and (self.post.version_current.pk == self.pk)
                and (self.status == PostStatus.PUBLISHED)
            )

            if not factors:
                print(
                    f"is active: {is_active}, close date: {self.closes_at}, current version pk: {self.post.version_current.pk} self pk: {self.pk} status: {self.status}"
                )

            return factors
        else:
            return False
