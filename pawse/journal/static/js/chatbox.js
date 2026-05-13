btn = document.getElementById("chat-btn");
chatBox = document.getElementById("chatbox");
chatOpen = false;

btn.addEventListener("click", () => {
    if (!chatOpen) {
        chatBox.removeAttribute("hidden");
        chatOpen = true;
    } else {
        chatBox.setAttribute("hidden", "");
        chatOpen = false;
    }
})