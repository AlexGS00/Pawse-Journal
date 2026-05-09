from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("journal/new/", views.create_entry, name="create_entry"),
    path("journal/<int:entry_id>/", views.entry_detail, name="entry_detail"),
    path("journal/<int:entry_id>/edit/", views.edit_entry, name="edit_entry"),
    path("register", views.register, name="register"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
]
