from google import genai
from openai import OpenAI
from django.conf import settings
from pgvector.django import CosineDistance
from .models import EntryChunck

gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENROUTER_API_KEY
)

CHAT_MODEL = "google/gemini-2.0-flash-001"

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

    flush()
    return chunks

def embedding_pipeline(entry: str):
    embeddings = []
    chuncks = entry_chunking(entry)

    for i, chunck in enumerate(chuncks):
        result = gemini_client.models.embed_content(
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
    query_embedding = gemini_client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=query,
        config={"output_dimensionality": 768}
    ).embeddings[0].values

    chunks = (
        EntryChunck.objects
        .filter(entry__user=user)
        .annotate(distance=CosineDistance("embedding", query_embedding))
        .order_by('distance')[:top_k]
    )

    return chunks

def summarize_entry(content: str) -> str:
    response = openrouter_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "user", "content": f"Summarize this journal entry in 2-3 sentences:\n\n{content}"}
        ]
    )
    return response.choices[0].message.content

def chat_stream(user_message, history, relevant_chunks, entry_summary=None):
    context = "\n\n---\n\n".join(chunk.content for chunk in relevant_chunks)

    system_prompt = f"You are a journaling assistant. Answer based on the user's journal entries.\n\nRelevant journal excerpts:\n{context}"

    if entry_summary:
        system_prompt += f"\n\nEntry summary:\n{entry_summary}"

    messages = [{"role": "system", "content": system_prompt}]

    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": user_message})

    return openrouter_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        stream=True
    )
