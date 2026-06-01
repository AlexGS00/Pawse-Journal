const chatBtn = document.getElementById("chat-btn");
const closeBtn = document.getElementById("chat-close-btn");
const chatBox = document.getElementById("chatbox");
const messagesEl = document.getElementById("chat-messages");
const emptyEl = document.getElementById("chat-empty");
const inputEl = document.getElementById("chat-input");
const sendBtn = document.getElementById("chat-send-btn");

const entryId = chatBox.dataset.entryId;
let conversationId = null;
let chatOpen = false;

function openChat() {
    chatBox.classList.remove("translate-x-full");
    document.body.classList.add("chat-open");
    chatBtn.textContent = "Close chat";
    chatOpen = true;
    inputEl.focus();
}

function closeChat() {
    chatBox.classList.add("translate-x-full");
    document.body.classList.remove("chat-open");
    chatBtn.textContent = "Start chat";
    chatOpen = false;
}

chatBtn.addEventListener("click", () => chatOpen ? closeChat() : openChat());
closeBtn.addEventListener("click", closeChat);

inputEl.addEventListener("input", () => {
    inputEl.style.height = "auto";
    inputEl.style.height = inputEl.scrollHeight + "px";
});

function setLoading(isLoading) {
    sendBtn.disabled = isLoading;
    inputEl.disabled = isLoading;
}

async function ensureConversation() {
    if (conversationId) return;
    const res = await fetch(`/journal/${entryId}/chat/start/`, {
        method: "POST",
        headers: { "X-CSRFToken": getCsrfToken() }
    });
    const data = await res.json();
    conversationId = data.conversation_id;
}

async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text) return;

    appendMessage(messagesEl, emptyEl, text, "user");
    inputEl.value = "";
    inputEl.style.height = "auto";
    setLoading(true);

    try {
        await ensureConversation();
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
