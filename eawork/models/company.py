from django.db import models
from typing import List
from eawork.models.user import User
from eawork.models.tag import JobPostTag, JobPostTagTypeEnum
from django.apps import apps
from django.utils import timezone
from datetime import timedelta


class Company(models.Model):
    name = models.CharField(max_length=128)
    id_external_80_000_hours = models.CharField(max_length=511, blank=True)
    description = models.TextField(blank=True)  # markdown
    description_short = models.TextField(blank=True)  # markdown
    logo_url = models.URLField(max_length=511, blank=True)

    internal_links = models.TextField(blank=True)  # markdown
    external_links = models.TextField(blank=True)  # markdown
    additional_commentary = models.TextField(blank=True)  # markdown

    url = models.URLField(max_length=511, blank=True)
    linkedin_url = models.URLField(max_length=511, blank=True, verbose_name="Linkedin")
    facebook_url = models.URLField(max_length=511, blank=True, verbose_name="Facebook")
    glassdoor_url = models.URLField(max_length=511, blank=True, verbose_name="Glassdoor")
    forum_url = models.URLField(max_length=511, blank=True, verbose_name="Forum")
    career_page_url = models.URLField(max_length=511, blank=True)

    is_top_recommended_org = models.BooleanField(default=False)
    year_founded = models.TextField(blank=True)
    social_media_links = models.TextField(blank=True)  # markdown
    org_size = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    text_hover = models.TextField(blank=True)  # markdown
    headquarters = models.ForeignKey(
        JobPostTag,
        limit_choices_to={"types__type": JobPostTagTypeEnum.LOCATION_80K},
        null=True,
        on_delete=models.SET_NULL,
    )

    tags_areas = models.ManyToManyField(
        JobPostTag,
        limit_choices_to={"types__type": JobPostTagTypeEnum.AREA},
        blank=True,
        related_name="tags_areas",
    )

    tags_locations = models.ManyToManyField(
        JobPostTag,
        limit_choices_to={"types__type": JobPostTagTypeEnum.LOCATION_80K},
        blank=True,
        related_name=f"tags_locations",
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "companies"

    def get_posts(self) -> List:
        posts = apps.get_model("eawork", "JobPost")

        arr = []
        for post in posts.objects.filter(company__name=self.name):
            vc = post.version_current

            is_active = True
            if vc.closes_at is not None:
                is_active = timezone.now() <= (vc.closes_at + timedelta(1))

            if is_active:
                d = {
                    "pk": vc.pk,
                    "title": vc.title,
                    "salary": vc.salary,
                    "visa_sponsorship": vc.visa_sponsorship,
                    "problem_areas": vc.get_tags_area_formatted(),
                    "experience_required": vc.get_tags_exp_required_formatted(),
                    "closes_at": vc.closes_at,
                }
                arr.append(d)

        return arr

    def get_post_count(self) -> int:
        posts = self.get_posts()
        return len(posts)

    def get_locations(self) -> list[str]:
        return [tag.name.replace(".", ", ") for tag in self.tags_locations.all()]

    def get_problem_areas(self) -> list[str]:
        return [tag.name for tag in self.tags_areas.all()]

    def get_hq(self) -> list[str]:
        if self.headquarters is None:
            return ""
        return self.headquarters.name
