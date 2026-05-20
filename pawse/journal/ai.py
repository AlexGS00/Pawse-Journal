from google import genai
from django.conf import settings

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
        