const messagesEl = document.getElementById("chat-messages");
const emptyEl = document.getElementById("chat-empty");
const inputEl = document.getElementById("chat-input");
const sendBtn = document.getElementById("chat-send-btn");

const rootEl = document.getElementById("conversation-root");
const conversationId = rootEl.dataset.conversationId;
const renameUrl = rootEl.dataset.renameUrl;

// --- Title editing ---
const titleEl = document.getElementById("conv-title");
const titleInputEl = document.getElementById("conv-title-input");
const titleEditBtn = document.getElementById("title-edit-btn");
const titleSaveBtn = document.getElementById("title-save-btn");
const titleCancelBtn = document.getElementById("title-cancel-btn");

function startEditTitle() {
    titleInputEl.value = titleEl.textContent;
    titleEl.classList.add("hidden");
    titleInputEl.classList.remove("hidden");
    titleEditBtn.classList.add("hidden");
    titleSaveBtn.classList.remove("hidden");
    titleCancelBtn.classList.remove("hidden");
    titleInputEl.focus();
    titleInputEl.select();
}

function cancelEditTitle() {
    titleEl.classList.remove("hidden");
    titleInputEl.classList.add("hidden");
    titleEditBtn.classList.remove("hidden");
    titleSaveBtn.classList.add("hidden");
    titleCancelBtn.classList.add("hidden");
}

async function saveTitle() {
    const newTitle = titleInputEl.value.trim();
    if (!newTitle) return;
    const res = await fetch(renameUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": getCsrfToken() },
        body: JSON.stringify({ title: newTitle }),
    });
    if (res.ok) {
        const data = await res.json();
        titleEl.textContent = data.title;
        document.title = data.title + " — Pawse";
        cancelEditTitle();
    }
}

titleEditBtn.addEventListener("click", startEditTitle);
titleSaveBtn.addEventListener("click", saveTitle);
titleCancelBtn.addEventListener("click", cancelEditTitle);
titleInputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter") saveTitle();
    if (e.key === "Escape") cancelEditTitle();
});

// Render existing assistant messages as markdown on load
document.querySelectorAll("[data-role='assistant']").forEach(bubble => {
    bubble.innerHTML = marked.parse(bubble.textContent);
    bubble.classList.remove("whitespace-pre-wrap");
    bubble.classList.add("markdown-content");
});

messagesEl.scrollTop = messagesEl.scrollHeight;

inputEl.addEventListener("input", () => {
    inputEl.style.height = "auto";
    inputEl.style.height = inputEl.scrollHeight + "px";
});

function setLoading(isLoading) {
    sendBtn.disabled = isLoading;
    inputEl.disabled = isLoading;
}

async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text) return;

    appendMessage(messagesEl, emptyEl, text, "user");
    inputEl.value = "";
    inputEl.style.height = "auto";
    setLoading(true);

    try {
        await sendAndStream(conversationId, text, messagesEl, emptyEl);
    } catch {
        appendMessage(messagesEl, emptyEl, "Something went wrong. Please try again.", "assistant");
    } finally {
        setLoading(false);
        inputEl.focus();
    }
}

sendBtn.addEventListener("click", sendMessage);

inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});
