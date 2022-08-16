from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=128, unique=True)
    linkedin_url = models.URLField(max_length=400, blank=True, verbose_name="Linkedin")
    facebook_url = models.URLField(max_length=400, blank=True, verbose_name="Facebook")
