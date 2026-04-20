from django.shortcuts import render
from django.contrib.auth import login, logout, authenticate

# Create your views here.
def index(request):
    return render(request, "journal/index.html")