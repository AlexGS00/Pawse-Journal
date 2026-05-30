# Pawse — Project Context

## Overview

Pawse is a multi-user AI-integrated digital journaling web app. The core idea is that journal entries serve as persistent context for AI conversations, eliminating the need to re-explain previously written thoughts. The name plays on "pause to reflect" with a cat theme.

Built as a portfolio project by a high school student. Prioritizes clean, working features over scope creep.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django |
| Database | Supabase (cloud Postgres) |
| Vector storage | pgvector (via Supabase) |
| Frontend | Django templates, Tailwind CSS, vanilla JavaScript |
| LLM | Gemini API free tier — `gemini-2.0-flash` via `google-genai` SDK |
| Embeddings | Gemini embeddings API — `gemini-embedding-001`, 768 dimensions |
| OCR | Gemini vision-capable model (TBD) |
| Auth | Django built-in auth |

**No React.** All interactivity is vanilla JS. Django handles server-side rendering.

---

## Current State

- Entry CRUD is fully functional (create, edit, delete, detail view)
- Embedding pipeline is complete: entries are chunked on save, each chunk embedded with `gemini-embedding-001` and stored as `EntryChunck` rows
- `summarize_entry()` is implemented in `ai.py` — called on create/edit, result stored in `Entry.summary`
- `get_relevant_chunks()` and `chat()` functions are written in `ai.py` — RAG retrieval and multi-turn Gemini chat
- Conversation/Message models exist in the DB; views, URLs, and chat UI are **not yet built**
- UI has an established vibe: minimal, warm, personal, classy. Do not deviate from this aesthetic.

---

## Data Models

### User
Standard Django user. All data (entries, tags, conversations) is scoped per user.

### JournalEntry
- `title` — string
- `content` — text
- `user` — FK to User
- `created_at` — datetime
- `updated_at` — datetime
- `tags` — M2M to Tag
- `summary` — short AI-generated summary (generated once on save, stored as text — essentials only, used as lightweight context injection)

### EntryChunk
- `entry` — FK to JournalEntry (CASCADE delete)
- `chunk_index` — integer, position of chunk within the entry
- `content` — the chunk's text (needed to inject into AI prompt)
- `embedding` — pgvector field, 768 dimensions (gemini-embedding-001)

> Note: model is named `EntryChunck` (with a typo) in the actual code.

### Tag
- `name` — string
- `color` — string (hex code or maps to a set of predetermined color names; user's choice at creation)
- `user` — FK to User (tags are per-user, not global)

### Conversation
- `title` — string (AI-generated on creation, editable by user)
- `original_entry` — FK to JournalEntry, **nullable** (`null=True, blank=True, on_delete=SET_NULL`) — null means standalone chat
- `user` — FK to User
- `created_at` — datetime
- `updated_at` — datetime

### Message
- `conversation` — FK to Conversation
- `role` — choices: 'user' | 'assistant'
- `content` — text
- `created_at` — datetime

---

## Entry Lifecycle

1. User fills out entry form (title, body, tags, optional OCR photos)
2. On save:
   - Entry stored in DB
   - A short essential-only summary is generated via OpenRouter and stored on the entry
   - Entry body is chunked and embedded via Gemini embeddings API; vectors stored in pgvector
3. Entry is always **read-only** in the view page. Editing requires clicking an Edit button which loads the form pre-populated with existing data.
4. Deleting an entry requires navigating into it and confirming via a "Are you sure?" dialog.

---

## Handwriting OCR (Entry Creation Only)

- Available only during entry creation/editing, not as a standalone feature.
- User can upload one or more photos of handwritten notes.
- Each photo is sent to a vision-capable model via OpenRouter for transcription.
- Transcribed text appears in an **editable textarea** so the user can correct errors before inserting it into the entry body.
- User can upload multiple photos sequentially, each producing its own correctable textarea.
- After correction, the text is appended/inserted into the main entry body.

---

## AI / RAG Pipeline

### Embedding Strategy
- On entry save, the body is chunked (paragraph or fixed-size chunks) and each chunk is embedded via Gemini embeddings API (`gemini-embedding-001`, 768 dimensions).
- Each chunk is stored as an `EntryChunck` row with its text and vector. No entry-level embedding — all retrieval happens at the chunk level.

### Context Injection Strategy (Hybrid, RAG-weighted)

When a conversation message is sent, context is assembled as follows:

1. **Current entry summary** (if chat is entry-bound): always injected. Short, essentials-only summary stored on the entry at save time. Low token cost.
2. **High-priority RAG from current entry** (if entry-bound): retrieve the most relevant chunks specifically from the current entry. These are weighted higher than general retrieval.
3. **General RAG across all user entries**: fill remaining context slots with the most relevant chunks from the rest of the journal, based on cosine similarity to the current message.

The intent is RAG-first, with the summary as a cheap anchor rather than a dominant source of context. Do not inject the full entry body — this is intentional to control token costs.

### Conversation Continuity
- Full message history of the conversation is re-sent to the LLM on each turn (standard multi-turn chat pattern).
- When a user returns to a past conversation, the stored message history is loaded and sent as context, so the AI has memory of what was previously discussed.

### Standalone Chat (No Entry)
- RAG still runs across all user entries based on message content.
- No current-entry priority weighting. General retrieval only.

---

## Pages & Features

### Entry List / Home
- Lists all user entries, newest first.
- Search bar: search by keyword in title only, or title + body (user selects scope).
- Tag filter bar: user can add/remove tags to filter by. Multiple tags can be active simultaneously.
- Keyword search in body is acceptable to implement as a DB text search (no need for a separate search index — standard Postgres `ILIKE` or full-text search is fine for portfolio scale).

### Entry View (Read-Only)
- Displays title, date, tags, body.
- Edit button → navigates to entry form pre-populated.
- Delete button → confirmation dialog → deletes entry and associated embeddings/chunks.
- **Chat Panel**: a button opens a collapsible chat panel on the right side of the screen. The entry content remains visible and readable on the left.
  - The chat panel is a live session. It is not automatically re-opened when returning to the entry.
  - The conversation is saved in the background as messages are sent.
  - Starting a new chat from an entry always creates a new Conversation with `original_entry` set.
  - You cannot start a new chat for an entry without leaving the entry first (i.e. one active chat session per entry view at a time).

### Entry Form (Create / Edit)
- Fields: title, body (textarea), tags.
- Tag input: shows existing user tags as selectable chips. Next to them, a "Create new tag" option opens an inline input for name + color (hex input or color picker with preset options).
- OCR section: "Add handwritten photo" button. Each uploaded photo triggers OCR transcription via a vision-capable model on OpenRouter and renders a correctable textarea. Multiple photos can be added sequentially. Corrected text is inserted into the entry body.

### Chat History
- Lists all conversations, grouped or sorted by last modified.
- Each conversation shows: title, origin entry (labeled something like "Started from: [entry title]" — or blank if standalone), created date, last modified date.
- Clicking a conversation opens the full chat view.
- A dropdown or search allows filtering conversations by original entry.
- "New Conversation" button → optional: pick an entry as context, or leave blank for standalone.

### Chat View
- Shows full message history.
- Input to continue the conversation.
- Link to origin entry if applicable.
- Edit conversation title inline.
- Delete conversation button with confirmation dialog.

### Auth Pages
- Register, Login, Logout — standard Django auth flow.

---

## Mobile Compatibility

The final version must be fully mobile-compatible. Design and implement with responsive layout from the start. The chat panel on entry view should stack vertically on mobile (chat below entry, or as a modal/drawer).

---

## Visual Design Principles

- Minimal but warm and personal — not cold or purely utilitarian.
- Classy, not playful/loud.
- Consistent with the existing UI already established in the project.
- Cat theme is present in the name/branding but should not dominate the UI.

---

## What This Project Is Not

- Not a startup MVP — it is a portfolio project. Scope accordingly.
- No social features, no sharing between users.
- No React — vanilla JS only for interactivity.
- No fine-tuning — RAG only for AI context.
- Do not over-engineer. Prefer simple and working over clever and broken.

---

## License

All Rights Reserved. Copyright (c) 2026.
