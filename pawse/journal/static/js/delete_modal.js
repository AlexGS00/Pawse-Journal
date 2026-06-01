function openDeleteModal(url, label) {
    document.getElementById("delete-modal-message").textContent =
        "Are you sure you want to delete this " + label + "?";
    document.getElementById("delete-modal-form").action = url;
    document.getElementById("delete-modal").classList.remove("hidden");
}

function closeDeleteModal() {
    document.getElementById("delete-modal").classList.add("hidden");
}

document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeDeleteModal();
});
