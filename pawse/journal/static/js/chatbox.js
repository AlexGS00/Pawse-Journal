const chatBtn = document.getElementById("chat-btn");
const closeBtn = document.getElementById("chat-close-btn");
const chatBox = document.getElementById("chatbox");
const messagesEl = document.getElementById("chat-messages");
const emptyEl = document.getElementById("chat-empty");
const inputEl = document.getElementById("chat-input");
const sendBtn = document.getElementById("chat-send-btn");
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

// Auto-resize textarea
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

function sendMessage() {
    const text = inputEl.value.trim();
    if (!text) return;

    appendMessage(text, "user");
    inputEl.value = "";
    inputEl.style.height = "auto";

    // TODO: wire up API call
}

sendBtn.addEventListener("click", sendMessage);

inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});
