from django.contrib import admin
from .models import Entry, EntryChunck, Tag, Conversation, Message

admin.site.register(Entry)
admin.site.register(EntryChunck)
admin.site.register(Tag)
admin.site.register(Conversation)
admin.site.register(Message)
