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

function getCsrfToken() {
    return document.cookie.split(';')
        .find(c => c.trim().startsWith('csrftoken='))
        ?.split('=')[1];
}

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

function appendMessage(text, role) {
    emptyEl.classList.add("hidden");

    const wrapper = document.createElement("div");
    wrapper.className = role === "user" ? "flex justify-end" : "flex justify-start";

    const bubble = document.createElement("div");
    bubble.className = role === "user"
        ? "max-w-[80%] px-4 py-2.5 bg-stone-800 text-stone-50 rounded-2xl rounded-br-sm text-sm leading-relaxed whitespace-pre-wrap"
        : "max-w-[80%] px-4 py-2.5 bg-white border border-stone-200 text-stone-800 rounded-2xl rounded-bl-sm text-sm leading-relaxed whitespace-pre-wrap";

    bubble.textContent = text;
    wrapper.appendChild(bubble);
    messagesEl.appendChild(wrapper);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function createAssistantBubble() {
    emptyEl.classList.add("hidden");

    const wrapper = document.createElement("div");
    wrapper.className = "flex justify-start";

    const bubble = document.createElement("div");
    bubble.className = "max-w-[80%] px-4 py-2.5 bg-white border border-stone-200 text-stone-800 rounded-2xl rounded-bl-sm text-sm leading-relaxed whitespace-pre-wrap";

    wrapper.appendChild(bubble);
    messagesEl.appendChild(wrapper);
    return bubble;
}

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

    appendMessage(text, "user");
    inputEl.value = "";
    inputEl.style.height = "auto";
    setLoading(true);

    try {
        await ensureConversation();

        const res = await fetch(`/conversation/${conversationId}/message/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken()
            },
            body: JSON.stringify({ message: text })
        });

        const bubble = createAssistantBubble();
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let rawText = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const parts = buffer.split("\n\n");
            buffer = parts.pop();

            for (const part of parts) {
                if (!part.startsWith("data: ")) continue;
                const data = JSON.parse(part.slice(6));
                if (data.token) {
                    rawText += data.token;
                    bubble.textContent = rawText;
                    messagesEl.scrollTop = messagesEl.scrollHeight;
                }
                if (data.done) {
                    bubble.innerHTML = marked.parse(rawText);
                    bubble.classList.remove("whitespace-pre-wrap");
                    bubble.classList.add("markdown-content");
                    messagesEl.scrollTop = messagesEl.scrollHeight;
                }
            }
        }
    } catch {
        appendMessage("Something went wrong. Please try again.", "assistant");
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
