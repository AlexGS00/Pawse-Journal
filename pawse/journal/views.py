from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.models import User
from .models import Entry


def index(request):
    entries = Entry.objects.filter(user=request.user) if request.user.is_authenticated else []
    return render(request, "journal/index.html", {"entries": entries})


def login_view(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username", "").strip(),
            password=request.POST.get("password", "").strip(),
        )
        if user:
            auth_login(request, user)
            return redirect("index")
        return render(request, "journal/login.html", {"error_message": "Invalid username or password"})
    return render(request, "journal/login.html")


def logout_view(request):
    auth_logout(request)
    return redirect("index")


def register(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        confirmation = request.POST.get("confirmation", "").strip()

        if password != confirmation:
            return render(request, "journal/register.html", {"error_message": "Passwords do not match"})
        if User.objects.filter(username=username).exists():
            return render(request, "journal/register.html", {"error_message": "Username already taken"})
        if User.objects.filter(email=email).exists():
            return render(request, "journal/register.html", {"error_message": "Email already in use"})

        user = User.objects.create_user(username=username, email=email, password=password)
        auth_login(request, user)
        return redirect("index")
    return render(request, "journal/register.html")


def entry_detail(request, entry_id):
    entry = get_object_or_404(Entry, id=entry_id, user=request.user)
    return render(request, "journal/entry_detail.html", {"entry": entry})


def edit_entry(request, entry_id):
    entry = get_object_or_404(Entry, id=entry_id, user=request.user)
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        if content:
            entry.title = title
            entry.content = content
            entry.save()
            return redirect("entry_detail", entry_id=entry.id)
    return render(request, "journal/create_entry.html", {"entry": entry})


def create_entry(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        if content:
            Entry.objects.create(user=request.user, title=title, content=content)
            return redirect("index")
    return render(request, "journal/create_entry.html")
