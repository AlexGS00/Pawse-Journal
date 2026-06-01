from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("journal/new/", views.create_entry, name="create_entry"),
    path("journal/<int:entry_id>/", views.entry_detail, name="entry_detail"),
    path("journal/<int:entry_id>/edit/", views.edit_entry, name="edit_entry"),
    path("chat/", views.chat_index, name="chat_index"),
    path("chat/start/", views.start_free_conversation, name="start_free_conversation"),
    path("conversation/<int:conversation_id>/", views.conversation_detail, name="conversation_detail"),
    path("journal/<int:entry_id>/chat/start/", views.start_conversation, name="start_conversation"),
    path("conversation/<int:conversation_id>/message/", views.send_message, name="send_message"),
    path("conversation/<int:conversation_id>/rename/", views.rename_conversation, name="rename_conversation"),
    path("conversation/<int:conversation_id>/delete/", views.delete_conversation, name="delete_conversation"),
    path("journal/<int:entry_id>/delete/", views.delete_entry, name="delete_entry"),
    path("register", views.register, name="register"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
]
