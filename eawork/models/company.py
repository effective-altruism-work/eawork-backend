from django.db import models

from eawork.models.user import User


class Company(models.Model):
    name = models.CharField(max_length=128)
    id_external_80_000_hours = models.CharField(max_length=511, blank=True)
    description = models.TextField(blank=True)
    logo_url = models.URLField(max_length=511, blank=True)
    url = models.URLField(max_length=511, blank=True)
    linkedin_url = models.URLField(max_length=511, blank=True, verbose_name="Linkedin")
    facebook_url = models.URLField(max_length=511, blank=True, verbose_name="Facebook")
    career_page_url = models.URLField(max_length=511, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name
