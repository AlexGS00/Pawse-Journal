import json
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Entry, Tag, EntryChunck, Conversation, Message
from django.db import transaction


from .ai import embedding_pipeline, summarize_entry, get_relevant_chunks, chat_stream


def index(request):
    entries = Entry.objects.filter(user=request.user) if request.user.is_authenticated else []
    return render(request, "journal/index.html", {"entries": entries})


def login_view(request):
    if request.method == "POST":
        identifier = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        
        username = identifier
        
        if "@" in username:
            try:
                username = User.objects.get(email__iexact=identifier).username
            except User.DoesNotExist:
                username = None
        
        user = authenticate(request, username=username, password=password) if username else None
        
        if user:
            auth_login(request, user)
            return redirect(index)
        
        return render(request, "journal/login.html", {"error_message": "Invalid username/email or password"})
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
            
            #check if content was modified
            if content != entry.content:
                entry.content = content
                entry.summary = summarize_entry(content)
                entry.save()
                
                #delete existing embedings for entry
                EntryChunck.objects.filter(entry=entry).delete()
                
                #create new embedings for entry
                for chunck in embedding_pipeline(entry.content):
                    EntryChunck.objects.create(entry=entry, chunck_index=chunck["index"], content=chunck["text"], embedding=chunck["embedding"])
                    
            else:   
                entry.save()
            return redirect("entry_detail", entry_id=entry.id)
    return render(request, "journal/create_entry.html", {"entry": entry})


def create_entry(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        if content:
            with transaction.atomic():
                entry = Entry(user=request.user, title=title, content=content)
                entry.summary = summarize_entry(content)
                entry.save()
                
                for chunck in embedding_pipeline(entry.content):
                    EntryChunck.objects.create(entry=entry, chunck_index=chunck["index"], content=chunck["text"], embedding=chunck["embedding"]) 
                
            return redirect("index")
    return render(request, "journal/create_entry.html")

@login_required
@require_POST
def start_conversation(request, entry_id):
    entry = get_object_or_404(Entry, id=entry_id, user=request.user)
    conversation = Conversation.objects.create(
        title=f"Chat about {entry.display_title()}",
        user = request.user,
        original_entry = entry
    )
    return JsonResponse({"conversation_id": conversation.id})

@login_required
@require_POST
def send_message(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    user_message = json.loads(request.body).get("message", "").strip()
    if not user_message:
        return JsonResponse({"error": "Empty message"}, status=400)

    Message.objects.create(conversation=conversation, role="user", content=user_message)

    history = list(conversation.messages.order_by("created_at"))[:-1]
    chunks = get_relevant_chunks(user_message, request.user)
    entry_summary = conversation.original_entry.summary if conversation.original_entry else None

    stream = chat_stream(user_message, history, chunks, entry_summary)

    def event_stream():
        full_reply = ""
        for chunk in stream:
            token = chunk.choices[0].delta.content or ""
            if token:
                full_reply += token
                yield f"data: {json.dumps({'token': token})}\n\n"
        Message.objects.create(conversation=conversation, role="assistant", content=full_reply)
        yield f"data: {json.dumps({'done': True})}\n\n"

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response