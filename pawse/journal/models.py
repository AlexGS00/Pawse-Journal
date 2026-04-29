from django.db import models
from django.contrib.auth.models import User


class Entry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='entries')
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title or self.created_at.strftime('%B %d, %Y')

    def display_title(self):
        return self.title if self.title else self.created_at.strftime('%B %d, %Y')

    def excerpt(self):
        if len(self.content) > 120:
            return self.content[:120].rstrip() + '…'
        return self.content
