from django.db import models
from django.contrib.auth.models import User
from pgvector.django import VectorField

from django.core.validators import RegexValidator

hex_color_validator = RegexValidator(
    regex = r'#[0-9A-Fa-f]{6}$',
    message="Enter a valid hex color code"
)
class Entry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='entries')
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField("Tag", blank=True, related_name="entries")
    summary = models.TextField(blank=True)

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

class EntryChunck(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name='chuncks')
    chunck_index = models.IntegerField()
    content = models.TextField()
    embedding = VectorField(dimensions=768)
class Tag(models.Model):
    name = models.CharField(max_length=30, blank=True)
    color = models.CharField(max_length=7, validators=[hex_color_validator])
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tags")

class Conversation(models.Model):
    title = models.CharField(max_length=128, blank=True)
    original_entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="conversations")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="conversations")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Message(models.Model):
    
    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant")
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)