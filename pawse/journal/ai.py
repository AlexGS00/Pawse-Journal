from google import genai
from django.conf import settings
from pgvector.django import CosineDistance
from .models import EntryChunck

client = genai.Client(api_key=settings.GEMINI_API_KEY)

def entry_chunking(entry: str) -> list[str]:
    MIN_CHUNK_SIZE = 300
    MAX_CHUNK_SIZE = 1000
    chunks = []
    current = []
    cur_len = 0

    def flush():
        if current:
            chunks.append(" ".join(current))
            current.clear()

    lines = entry.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        is_blank = not stripped
        is_last = i == len(lines) - 1

        if is_blank:
            if cur_len >= MIN_CHUNK_SIZE:
                flush()
                cur_len = 0
        else:
            current.append(stripped)
            cur_len += len(stripped)
            if cur_len >= MAX_CHUNK_SIZE or is_last:
                flush()
                cur_len = 0

    flush()  # catch anything remaining
    return chunks

def embedding_pipeline(entry: str):
    embeddings = []
    chuncks = entry_chunking(entry)
    
    for i, chunck in enumerate(chuncks):
        result = client.models.embed_content(
            model="models/gemini-embedding-001",
            contents=chunck,
            config={"output_dimensionality": 768}
        )
        vector = result.embeddings[0].values
        embeddings.append({
            "index": i,
            "text": chunck,
            "embedding": vector
        })
    
    return embeddings
        
def get_relevant_chunks(query, user, top_k=5):
    query_embedding = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=query,
        config={"output_dimensionality" : 768}
    ).embeddings[0].values
    
    chunks = (
        EntryChunck.objects
        .filter(entry_user=user)
        .annotate(distance=CosineDistance("embedding", query_embedding))
        .order_by('distance')[:top_k]
    )
    
    return chunks

def chat(user_message, history, relevant_chunks, entry_summary=None):
    context = "\n\n---\n\n".join(chunk.content for chunk in relevant_chunks)
    
    system_prompt = f"You are a journaling assistant. Answer based on the user's journal entries. \n\nRelevant journal excerps:\n{context}"
    
    if entry_summary:
        system_prompt += f"\n\nEntry summary:\n{entry_summary}"
        
    gemini_history = [
        {
            "role" : "model" if msg.role == "assistant" else "user",
            "parts" : [{"text" : msg.content}]
        }
        for msg in history
    ]
    
    conversation = client.chats.create(
        model="gemini-2.0-flash",
        history=gemini_history,
        config={"system_instruction": system_prompt}
    )
    
    response = conversation.send_message(user_message)
    return response.text

