
function changeLanguage(language) {
    if (language !== "en" && language !== "hi") return;

    localStorage.setItem("panchayat_language", language);
    applyLanguage(language);
}

function applyLanguage(language) {
    document.documentElement.lang = language;

    document.querySelectorAll("[data-en][data-hi]").forEach(element => {
        const translation = element.getAttribute(`data-${language}`);

        if (translation !== null) {
            element.textContent = translation;
        }
    });

    document.querySelectorAll("[data-en-placeholder][data-hi-placeholder]").forEach(element => {
        element.placeholder = element.getAttribute(
            `data-${language}-placeholder`
        );
    });

    const englishButton = document.getElementById("englishBtn");
    const hindiButton = document.getElementById("hindiBtn");

    if (englishButton && hindiButton) {
        englishButton.classList.toggle("active", language === "en");
        hindiButton.classList.toggle("active", language === "hi");
    }

    const chatMessage = document.getElementById("chatMessage");

    if (chatMessage) {
        chatMessage.placeholder = language === "hi"
            ? "अपना सवाल पूछें..."
            : "Ask your question...";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const savedLanguage = localStorage.getItem("panchayat_language") || "hi";

    applyLanguage(savedLanguage);

    const chatToggle = document.getElementById("chatToggle");
    const chatClose = document.getElementById("chatClose");
    const chatBox = document.getElementById("chatBox");
    const chatForm = document.getElementById("chatForm");
    const chatBody = document.getElementById("chatBody");
    const chatMessage = document.getElementById("chatMessage");

    if (chatToggle && chatBox) {
        chatToggle.addEventListener("click", () => {
            chatBox.classList.toggle("active");
        });
    }

    if (chatClose && chatBox) {
        chatClose.addEventListener("click", () => {
            chatBox.classList.remove("active");
        });
    }

    function addMessage(message, type) {
        const div = document.createElement("div");

        div.className = type === "user"
            ? "user-message"
            : "bot-message";

        div.textContent = message;
        chatBody.appendChild(div);
        chatBody.scrollTop = chatBody.scrollHeight;

        return div;
    }

    if (chatForm) {
        chatForm.addEventListener("submit", async event => {
            event.preventDefault();

            const question = chatMessage.value.trim();

            if (!question) return;

            addMessage(question, "user");
            chatMessage.value = "";
            chatMessage.disabled = true;

            const loadingText =
                localStorage.getItem("panchayat_language") === "hi"
                ? "AI जवाब तैयार कर रहा है..."
                : "AI is thinking...";

            const loading = addMessage(loadingText, "bot");

            try {
                const response = await fetch("/api/chat", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        message: question,
                        language: localStorage.getItem("panchayat_language") || "hi"
                    })
                });

                const data = await response.json();

                loading.textContent = data.reply ||
                    "No response received.";

            } catch (error) {
                loading.textContent =
                    localStorage.getItem("panchayat_language") === "hi"
                    ? "AI सर्वर से कनेक्शन नहीं हो पाया।"
                    : "Unable to connect to AI server.";

            } finally {
                chatMessage.disabled = false;
                chatMessage.focus();
                chatBody.scrollTop = chatBody.scrollHeight;
            }
        });
    }
});

