function getCsrfToken() {
    return document.cookie.split(';')
        .find(c => c.trim().startsWith('csrftoken='))
        ?.split('=')[1];
}

function appendMessage(messagesEl, emptyEl, text, role) {
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

function createAssistantBubble(messagesEl, emptyEl) {
    emptyEl.classList.add("hidden");

    const wrapper = document.createElement("div");
    wrapper.className = "flex justify-start";

    const bubble = document.createElement("div");
    bubble.className = "max-w-[80%] px-4 py-2.5 bg-white border border-stone-200 text-stone-800 rounded-2xl rounded-bl-sm text-sm leading-relaxed whitespace-pre-wrap";

    wrapper.appendChild(bubble);
    messagesEl.appendChild(wrapper);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return bubble;
}

async function sendAndStream(conversationId, text, messagesEl, emptyEl) {
    const res = await fetch(`/conversation/${conversationId}/message/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrfToken()
        },
        body: JSON.stringify({ message: text })
    });

    const bubble = createAssistantBubble(messagesEl, emptyEl);
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
}
