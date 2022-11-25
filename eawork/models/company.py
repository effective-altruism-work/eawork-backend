from django.db import models
from typing import List
from eawork.models.user import User
from eawork.models.tag import JobPostTag, JobPostTagTypeEnum
from django.apps import apps
from django.utils import timezone


class Company(models.Model):
    name = models.CharField(max_length=128)
    id_external_80_000_hours = models.CharField(max_length=511, blank=True)
    description = models.TextField(blank=True)
    logo_url = models.URLField(max_length=511, blank=True)
    url = models.URLField(max_length=511, blank=True)
    linkedin_url = models.URLField(max_length=511, blank=True, verbose_name="Linkedin")
    facebook_url = models.URLField(max_length=511, blank=True, verbose_name="Facebook")
    career_page_url = models.URLField(max_length=511, blank=True)
    forum_url = models.URLField(max_length=511, blank=True, verbose_name="Forum")
    is_top_recommended_org = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    text_hover = models.TextField(blank=True)

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
                is_active = timezone.now() <= vc.closes_at

            if is_active:
                d = {"pk": vc.pk, "title": vc.title}
                arr.append(d)

        return arr

    # def get_locations(self) -> List:
    #     posts = apps.get_model("eawork", "JobPost")
    #     arr = []
    #     for post in posts.objects.filter(company__name=self.name):
    #         vc = post.version_current

    #         is_active = True
    #         if vc.closes_at is not None:
    #             is_active = timezone.now() <= vc.closes_at

    #         if is_active:
    #             locations = vc.get_tags_location_80k_formatted()
    #             for location in locations:
    #                 if location not in arr:
    #                     arr.append(location)

    #     return arr

    # def get_problem_areas(self) -> List:
    #     posts = apps.get_model("eawork", "JobPost")
    #     arr = []
    #     for post in posts.objects.filter(company__name=self.name):
    #         vc = post.version_current

    #         is_active = True
    #         if vc.closes_at is not None:
    #             is_active = timezone.now() <= vc.closes_at

    #         if is_active:
    #             prob_areas = vc.get_tags_area_formatted()
    #             for area in prob_areas:
    #                 if area not in arr:
    #                     arr.append(area)

    #     return arr
