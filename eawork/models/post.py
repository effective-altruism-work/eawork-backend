from django.db import models

from eawork.models.user import User


class Post(models.Model):
    # version_current = models.OneToOneField(
    #     "eawork.PostVersion",
    #     null=True,
    #     on_delete=models.SET_NULL,
    #     related_query_name="post_current",
    # )
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        if self.version_current:
            return self.version_current.title
        else:
            return str(self.pk)


class PostVersion(models.Model):
    # post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="versions")

    title = models.CharField(max_length=511)
    description = models.TextField(blank=True)

    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.title
