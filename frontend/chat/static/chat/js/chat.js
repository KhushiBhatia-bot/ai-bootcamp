const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

const accessToken = localStorage.getItem("access_token");

if (!accessToken) {
    window.location.href = "/";
}

let currentChatId = localStorage.getItem("current_chat_id");
if (currentChatId && currentChatId !== "null" && currentChatId !== "undefined") {
    currentChatId = Number(currentChatId);
} else {
    currentChatId = null;
}

let allChats = [];
let activeTagFilter = "all";
let attachedDocument = null; // { filename: string, text: string, char_count: number }

// ============================================================
// HTML Escaping Helpers
// ============================================================
function escapeHtml(text) {
    if (!text) return "";
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function escapeAttribute(text) {
    return escapeHtml(text);
}

/**
 * Remove lone Unicode surrogates and null bytes from text before
 * embedding in JSON payloads. Lone surrogates (U+D800–U+DFFF)
 * cause JSON.stringify() to throw in modern browsers.
 */
function sanitizeTextForJson(text) {
    if (!text) return "";
    // Remove null bytes
    text = text.replace(/\x00/g, "");
    // Replace lone surrogates with replacement character
    // Lone high surrogate not followed by low surrogate, or
    // low surrogate not preceded by high surrogate
    text = text.replace(/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/g, "\uFFFD");
    return text;
}

// ============================================================
// Custom In-App Modal Dialogs (Replaces native browser popups)
// ============================================================
function showConfirmDialog({
    title = "Confirm Action",
    message = "Are you sure you want to proceed?",
    confirmLabel = "Confirm",
    cancelLabel = "Cancel",
    isDanger = false,
}) {
    return new Promise((resolve) => {
        const overlay = document.createElement("div");
        overlay.className = "custom-dialog-overlay";
        overlay.innerHTML = `
            <div class="custom-dialog-card">
                <div class="custom-dialog-title">${escapeHtml(title)}</div>
                <div class="custom-dialog-message">${escapeHtml(message)}</div>
                <div class="custom-dialog-actions">
                    <button class="dialog-btn dialog-cancel" type="button">${escapeHtml(cancelLabel)}</button>
                    <button class="dialog-btn ${isDanger ? 'dialog-danger' : 'dialog-confirm'}" type="button">${escapeHtml(confirmLabel)}</button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        const confirmBtn = overlay.querySelector(isDanger ? ".dialog-danger" : ".dialog-confirm");
        const cancelBtn = overlay.querySelector(".dialog-cancel");

        let keyboardEnabled = false;

        const cleanup = (value) => {
            overlay.classList.add("closing");
            setTimeout(() => {
                if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
            }, 140);
            document.removeEventListener("keydown", onKeyDown);
            resolve(value);
        };

        const onKeyDown = (e) => {
            if (!keyboardEnabled) return; // Ignore until safe
            if (e.key === "Escape") { e.preventDefault(); cleanup(false); }
            if (e.key === "Enter") { e.preventDefault(); cleanup(true); }
        };

        // Delay enabling keyboard shortcuts to avoid carry-over key events
        // from the click that opened the dialog
        setTimeout(() => {
            keyboardEnabled = true;
            confirmBtn.focus();
        }, 300);

        document.addEventListener("keydown", onKeyDown);
        cancelBtn.addEventListener("click", () => cleanup(false));
        confirmBtn.addEventListener("click", () => cleanup(true));
        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) cleanup(false);
        });
    });
}

function showInputDialog({
    title = "Input Required",
    message = "",
    defaultValue = "",
    placeholder = "",
    confirmLabel = "Save",
    cancelLabel = "Cancel",
}) {
    return new Promise((resolve) => {
        const overlay = document.createElement("div");
        overlay.className = "custom-dialog-overlay";
        overlay.innerHTML = `
            <div class="custom-dialog-card">
                <div class="custom-dialog-title">${escapeHtml(title)}</div>
                ${message ? `<div class="custom-dialog-message">${escapeHtml(message)}</div>` : ""}
                <input type="text" class="custom-dialog-input" placeholder="${escapeAttribute(placeholder)}" value="${escapeAttribute(defaultValue)}" />
                <div class="custom-dialog-actions">
                    <button class="dialog-btn dialog-cancel" type="button">${escapeHtml(cancelLabel)}</button>
                    <button class="dialog-btn dialog-confirm" type="button">${escapeHtml(confirmLabel)}</button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        const input = overlay.querySelector(".custom-dialog-input");
        const confirmBtn = overlay.querySelector(".dialog-confirm");
        const cancelBtn = overlay.querySelector(".dialog-cancel");

        const cleanup = (value) => {
            overlay.classList.add("closing");
            setTimeout(() => {
                if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
            }, 140);
            document.removeEventListener("keydown", onKeyDown);
            resolve(value);
        };

        const onKeyDown = (e) => {
            if (e.key === "Escape") cleanup(null);
            if (e.key === "Enter") cleanup(input.value.trim());
        };

        document.addEventListener("keydown", onKeyDown);
        cancelBtn.addEventListener("click", () => cleanup(null));
        confirmBtn.addEventListener("click", () => cleanup(input.value.trim()));
        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) cleanup(null);
        });

        setTimeout(() => {
            input.focus();
            input.select();
        }, 50);
    });
}

// ============================================================
// Toast Notification (For background actions like mode switch)
// ============================================================
let toastTimeout = null;
function showToast(message, icon = "✓") {
    const toast = document.getElementById("toast-notification");
    if (!toast) return;

    toast.textContent = `${icon} ${message}`;
    toast.classList.add("show");

    if (toastTimeout) clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => {
        toast.classList.remove("show");
    }, 2400);
}

// ============================================================
// Theme Handling (Dark / Light Mode)
// ============================================================
function initTheme() {
    const savedTheme = localStorage.getItem("theme") || "light";
    document.documentElement.setAttribute("data-theme", savedTheme);
    updateThemeToggleIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute("data-theme") || "light";
    const newTheme = currentTheme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", newTheme);
    localStorage.setItem("theme", newTheme);
    updateThemeToggleIcon(newTheme);
    showToast(`Switched to ${newTheme} mode`, newTheme === "dark" ? "🌙" : "☀️");
}

function updateThemeToggleIcon(theme) {
    const btn = document.getElementById("theme-toggle");
    if (btn) {
        btn.textContent = theme === "dark" ? "☀️ Light" : "🌙 Dark";
    }
}

// ============================================================
// API Calls
// ============================================================

async function getChats() {
    const response = await apiFetch(`${API_BASE_URL}/chats/`);
    if (!response.ok) {
        throw new Error("Could not load chats");
    }
    return await response.json();
}

async function createChat(title = "New Chat", tag = null) {
    const response = await apiFetch(`${API_BASE_URL}/chats/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            title: title,
            tag: tag,
        }),
    });

    if (!response.ok) {
        throw new Error("Could not create chat");
    }

    return await response.json();
}

async function updateChatApi(chatId, updateData) {
    const response = await apiFetch(`${API_BASE_URL}/chats/${chatId}`, {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(updateData),
    });

    if (!response.ok) {
        throw new Error("Could not update chat");
    }

    return await response.json();
}

async function getMessages(chatId) {
    const response = await apiFetch(`${API_BASE_URL}/chats/${chatId}/messages/`);
    if (!response.ok) {
        throw new Error("Could not load messages");
    }
    return await response.json();
}

async function deleteChatApi(chatId) {
    const response = await apiFetch(`${API_BASE_URL}/chats/${chatId}`, {
        method: "DELETE",
    });

    if (!response.ok) {
        throw new Error("Could not delete chat");
    }
}

async function deleteMessage(chatId, messageId) {
    const response = await apiFetch(
        `${API_BASE_URL}/chats/${chatId}/messages/${messageId}`,
        {
            method: "DELETE",
        }
    );

    if (!response.ok) {
        throw new Error("Could not delete message");
    }
}

async function uploadDocApi(file) {
    const token = localStorage.getItem("access_token");
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/documents/upload`, {
        method: "POST",
        headers: {
            Authorization: `Bearer ${token}`,
        },
        body: formData,
    });

    if (!response.ok) {
        let errorMsg = "Failed to upload file";
        try {
            const err = await response.json();
            if (typeof err.detail === "string") {
                errorMsg = err.detail;
            } else if (Array.isArray(err.detail) && err.detail[0]?.msg) {
                errorMsg = err.detail[0].msg;
            }
        } catch (_) {}
        throw new Error(errorMsg);
    }

    return await response.json();
}

// ============================================================
// Chat List & Sidebar Management (Rename, Pin, Tag Filter)
// ============================================================

async function loadChats() {
    allChats = await getChats();
    renderChatList();
}

function renderChatList() {
    const chatList = document.getElementById("chat-list");
    chatList.innerHTML = "";

    const filteredChats = allChats.filter((chat) => {
        if (activeTagFilter === "all") return true;
        return chat.tag === activeTagFilter;
    });

    if (filteredChats.length === 0) {
        chatList.innerHTML = `<div class="no-chats">No conversations found</div>`;
        return;
    }

    filteredChats.forEach((chat) => {
        const chatItem = document.createElement("div");
        chatItem.className = "chat-item";

        if (chat.id === currentChatId) {
            chatItem.classList.add("active");
        }

        chatItem.innerHTML = `
            <div class="chat-item-content">
                <div class="chat-title-row">
                    ${chat.is_pinned ? `<span class="pin-indicator" title="Pinned conversation">📌</span>` : ""}
                    <span class="chat-title" title="${escapeAttribute(chat.title)}">
                        ${escapeHtml(chat.title)}
                    </span>
                </div>
                ${chat.tag ? `<span class="chat-tag-badge">${escapeHtml(chat.tag)}</span>` : ""}
            </div>

            <div class="chat-actions">
                <button class="chat-action-btn pin-chat" title="${chat.is_pinned ? "Unpin chat" : "Pin chat"}">
                    ${chat.is_pinned ? "📍" : "📌"}
                </button>
                <button class="chat-action-btn tag-chat" title="Change Category/Tag">
                    🏷️
                </button>
                <button class="chat-action-btn rename-chat" title="Rename chat">
                    ✏️
                </button>
                <button class="chat-action-btn delete-chat" title="Delete chat">
                    ×
                </button>
            </div>
        `;

        // Click to Open Chat
        chatItem.querySelector(".chat-item-content").addEventListener("click", async () => {
            await openChat(chat.id);
        });

        // Pin / Unpin
        chatItem.querySelector(".pin-chat").addEventListener("click", async (event) => {
            event.stopPropagation();
            try {
                await updateChatApi(chat.id, { is_pinned: !chat.is_pinned });
                showToast(chat.is_pinned ? "Chat unpinned" : "Chat pinned to top", "📌");
                await loadChats();
            } catch (err) {
                console.error(err);
                showToast("Failed to update pin", "⚠️");
            }
        });

        // Tag / Category
        chatItem.querySelector(".tag-chat").addEventListener("click", async (event) => {
            event.stopPropagation();
            const chosenTag = await showInputDialog({
                title: "Organize Conversation",
                message: "Enter a tag or folder name (e.g. AI, Economics, Biology) or leave empty to clear:",
                defaultValue: chat.tag || "",
                placeholder: "Tag name...",
                confirmLabel: "Save Tag",
            });
            if (chosenTag === null) return;

            try {
                await updateChatApi(chat.id, { tag: chosenTag.trim() || null });
                showToast(chosenTag.trim() ? `Tagged as "${chosenTag.trim()}"` : "Tag cleared", "🏷️");
                await loadChats();
                if (currentChatId === chat.id) updateHeaderTitle(chat.title, chosenTag.trim());
            } catch (err) {
                console.error(err);
                showToast("Failed to update tag", "⚠️");
            }
        });

        // Rename
        chatItem.querySelector(".rename-chat").addEventListener("click", async (event) => {
            event.stopPropagation();
            const newTitle = await showInputDialog({
                title: "Rename Conversation",
                message: "Enter a new title for this conversation:",
                defaultValue: chat.title,
                placeholder: "Conversation title...",
                confirmLabel: "Rename",
            });
            if (!newTitle || newTitle.trim() === chat.title) return;

            try {
                await updateChatApi(chat.id, { title: newTitle.trim() });
                showToast("Chat renamed", "✏️");
                await loadChats();
                if (currentChatId === chat.id) updateHeaderTitle(newTitle.trim(), chat.tag);
            } catch (err) {
                console.error(err);
                showToast("Failed to rename chat", "⚠️");
            }
        });

        // Delete Chat
        chatItem.querySelector(".delete-chat").addEventListener("click", async (event) => {
            event.stopPropagation();
            await removeChat(chat.id);
        });

        chatList.appendChild(chatItem);
    });
}

// Filter Tag Chips
document.querySelectorAll(".tag-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
        document.querySelectorAll(".tag-chip").forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");
        activeTagFilter = chip.dataset.tag;
        renderChatList();
    });
});

// Update Header Title & Tag Pill
function updateHeaderTitle(title, tag = null) {
    const titleElem = document.getElementById("current-chat-title");
    const tagElem = document.getElementById("current-chat-tag");

    if (titleElem) titleElem.textContent = title || "ResearchMate";
    if (tagElem) {
        if (tag) {
            tagElem.textContent = tag;
            tagElem.style.display = "inline-block";
        } else {
            tagElem.style.display = "none";
        }
    }
}

// ============================================================
// Open Existing Chat
// ============================================================

async function openChat(chatId) {
    currentChatId = chatId;
    localStorage.setItem("current_chat_id", chatId);

    const chat = allChats.find((c) => c.id === chatId);
    if (chat) updateHeaderTitle(chat.title, chat.tag);

    const messages = document.getElementById("messages");
    messages.innerHTML = `<div class="loading-chat">Loading conversation...</div>`;

    try {
        const chatMessages = await getMessages(chatId);
        messages.innerHTML = "";

        if (chatMessages.length === 0) {
            showWelcome();
        } else {
            chatMessages.forEach((message) => {
                if (message.role === "user") {
                    addUserMessage(message.content, message.id);
                } else {
                    addAssistantMessage(message.content, [], [], message.id);
                }
            });
        }

        renderChatList();
    } catch (error) {
        console.error(error);
        messages.innerHTML = `<div class="error-message">Could not load this conversation.</div>`;
    }
}

// ============================================================
// Delete Chat
// ============================================================

async function removeChat(chatId) {
    const confirmed = await showConfirmDialog({
        title: "Delete Conversation?",
        message: "This will permanently remove this conversation and its message history.",
        confirmLabel: "Delete",
        cancelLabel: "Cancel",
        isDanger: true,
    });
    if (!confirmed) return;

    try {
        await deleteChatApi(chatId);
        showToast("Conversation deleted", "🗑️");

        if (currentChatId === chatId) {
            currentChatId = null;
            localStorage.removeItem("current_chat_id");
            updateHeaderTitle("ResearchMate", null);
            showWelcome();
        }
        await loadChats();
    } catch (error) {
        console.error(error);
        showToast("Could not delete conversation", "⚠️");
    }
}

// ============================================================
// New Chat
// ============================================================

function startNewChat() {
    currentChatId = null;
    localStorage.removeItem("current_chat_id");
    updateHeaderTitle("ResearchMate", null);
    showWelcome();
    document.getElementById("message-input").focus();
    renderChatList();
}

// ============================================================
// Document Attachment & Question Answering
// ============================================================

const docUploadInput = document.getElementById("doc-upload-input");
const attachDocBtn = document.getElementById("attach-doc-btn");
const docPreviewBar = document.getElementById("doc-preview-bar");
const docFilenameElem = document.getElementById("doc-filename");
const docCharCountElem = document.getElementById("doc-char-count");
const removeDocBtn = document.getElementById("remove-doc-btn");

if (attachDocBtn && docUploadInput) {
    attachDocBtn.addEventListener("click", () => {
        docUploadInput.click();
    });

    docUploadInput.addEventListener("change", async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        showToast(`Processing ${file.name}...`, "⏳");

        try {
            const data = await uploadDocApi(file);
            attachedDocument = data;

            docFilenameElem.textContent = data.filename;
            docCharCountElem.textContent = `(${data.char_count.toLocaleString()} chars extracted)`;
            docPreviewBar.style.display = "flex";

            showToast(`Attached: ${data.filename}`, "📄");
            document.getElementById("message-input").focus();
        } catch (err) {
            console.error(err);
            showToast(err.message || "Failed to parse document", "⚠️");
        } finally {
            docUploadInput.value = "";
        }
    });
}

if (removeDocBtn) {
    removeDocBtn.addEventListener("click", () => {
        attachedDocument = null;
        docPreviewBar.style.display = "none";
        showToast("Document detached", "🗑️");
    });
}

// ============================================================
// UI Rendering
// ============================================================

function showWelcome() {
    const messagesContainer = document.getElementById("messages");
    messagesContainer.innerHTML = `
        <div class="welcome">
            <h2>What can I help you research?</h2>
            <p>
                Ask a question or upload a PDF / document to analyze. I search the web and synthesize reports with citations.
            </p>
        </div>
    `;
}

function addUserMessage(content, messageId = null) {
    const messagesContainer = document.getElementById("messages");
    const message = document.createElement("div");
    message.className = "message user-message";

    message.innerHTML = `
        <div class="message-header">
            <div class="message-label">You</div>
            <div class="message-actions">
                <button class="copy-btn" title="Copy text">📋 Copy</button>
                ${messageId ? `<button class="delete-message" data-id="${messageId}" title="Delete message">×</button>` : ""}
            </div>
        </div>
        <div class="message-content">${escapeHtml(content)}</div>
    `;

    const copyBtn = message.querySelector(".copy-btn");
    copyBtn.addEventListener("click", () => copyText(content, copyBtn));
    messagesContainer.appendChild(message);
    scrollToBottom();
}

function addAssistantMessage(
    content,
    sources = [],
    toolsUsed = [],
    messageId = null
) {
    const messagesContainer = document.getElementById("messages");
    const message = document.createElement("div");
    message.className = "message assistant-message";

    let sourcesHtml = "";
    if (sources && sources.length > 0) {
        sourcesHtml = `
            <div class="sources">
                <div class="sources-title">🔎 Sources</div>
                ${sources.map((source) => `
                    <div class="source">
                        <a href="${escapeAttribute(source.url)}" target="_blank" rel="noopener noreferrer">
                            ${escapeHtml(source.title)}
                        </a>
                        <p>${escapeHtml(source.snippet || "")}</p>
                    </div>
                `).join("")}
            </div>
        `;
    }

    let toolsHtml = "";
    if (toolsUsed && toolsUsed.length > 0) {
        toolsHtml = `<div class="tools-used">🔧 Used: ${toolsUsed.join(", ")}</div>`;
    }

    message.innerHTML = `
        <div class="message-header">
            <div class="message-label">ResearchMate</div>
            <div class="message-actions">
                <button class="copy-btn" title="Copy response">📋 Copy</button>
                ${messageId ? `<button class="delete-message" data-id="${messageId}" title="Delete message">×</button>` : ""}
            </div>
        </div>
        <div class="message-content markdown-content">
            ${marked.parse(content)}
        </div>
        ${toolsHtml}
        ${sourcesHtml}
    `;

    const copyBtn = message.querySelector(".copy-btn");
    copyBtn.addEventListener("click", () => copyText(content, copyBtn));
    messagesContainer.appendChild(message);
    scrollToBottom();
}

// ============================================================
// Real-Time Streaming Message Handler
// ============================================================

async function streamSendMessage(content) {
    let messagePayload = content;

    // If a document is attached, inject its context into the prompt
    if (attachedDocument) {
        // Sanitize document text to remove lone surrogates / null bytes
        // that would cause JSON.stringify() to fail or produce invalid JSON
        const safeText = sanitizeTextForJson(attachedDocument.text || "");
        messagePayload = `[Attached Document: "${attachedDocument.filename}"]\n\`\`\`\n${safeText}\n\`\`\`\n\nUser Question/Instruction: ${content}`;
        // Detach document after injecting into the message
        attachedDocument = null;
        docPreviewBar.style.display = "none";
    }

    if (!currentChatId) {
        const chatTitle = content.length > 35 ? content.substring(0, 35) + "..." : content;
        const tag = activeTagFilter !== "all" ? activeTagFilter : null;
        const chat = await createChat(chatTitle, tag);
        currentChatId = chat.id;
        localStorage.setItem("current_chat_id", currentChatId);
        updateHeaderTitle(chat.title, chat.tag);
        await loadChats();
    }

    const messagesContainer = document.getElementById("messages");

    // Create placeholder assistant message element
    const assistantMsgElem = document.createElement("div");
    assistantMsgElem.className = "message assistant-message";
    assistantMsgElem.innerHTML = `
        <div class="message-header">
            <div class="message-label">ResearchMate</div>
            <div class="message-actions">
                <button class="copy-btn" title="Copy response">📋 Copy</button>
                <button class="delete-message" title="Delete message" style="display:none;">×</button>
            </div>
        </div>
        <div class="agent-status-box" id="agent-status">
            <span class="spinner"></span>
            <span id="agent-status-text">Starting research...</span>
            <span id="agent-status-timer" style="margin-left:8px;opacity:0.55;font-size:0.82em;">0s</span>
        </div>
        <div class="message-content markdown-content" id="streaming-content"></div>
        <div id="streaming-tools" class="tools-used" style="display:none;"></div>
        <div id="streaming-sources" class="sources" style="display:none;"></div>
    `;

    messagesContainer.appendChild(assistantMsgElem);
    scrollToBottom();

    const statusBox = assistantMsgElem.querySelector("#agent-status");
    const statusText = assistantMsgElem.querySelector("#agent-status-text");
    const statusTimer = assistantMsgElem.querySelector("#agent-status-timer");

    // Live elapsed time counter
    const streamStart = Date.now();
    const timerInterval = setInterval(() => {
        if (!statusBox || !statusBox.parentNode) { clearInterval(timerInterval); return; }
        const elapsed = ((Date.now() - streamStart) / 1000).toFixed(0);
        if (statusTimer) statusTimer.textContent = `${elapsed}s`;
    }, 1000);
    const contentElem = assistantMsgElem.querySelector("#streaming-content");
    const toolsElem = assistantMsgElem.querySelector("#streaming-tools");
    const sourcesElem = assistantMsgElem.querySelector("#streaming-sources");
    const copyBtn = assistantMsgElem.querySelector(".copy-btn");
    const deleteBtn = assistantMsgElem.querySelector(".delete-message");

    let accumulatedText = "";
    let accumulatedSources = [];
    let accumulatedTools = [];

    copyBtn.addEventListener("click", () => copyText(accumulatedText, copyBtn));

    const token = localStorage.getItem("access_token");
    const bodyPayload = JSON.stringify({ content: messagePayload });
    console.log(`[Stream] Sending to chat ${currentChatId}, payload size: ${bodyPayload.length} bytes, content length: ${messagePayload.length} chars`);
    const response = await fetch(
        `${API_BASE_URL}/chats/${currentChatId}/messages/stream`,
        {
            method: "POST",
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json",
            },
            body: bodyPayload,
        }
    );

    if (!response.ok) {
        clearInterval(timerInterval);
        if (statusBox && statusBox.parentNode) {
            statusBox.remove();
        }
        let errorMsg = "Error connecting to research service.";
        try {
            const err = await response.json();
            console.error(`[Stream] ${response.status} error:`, JSON.stringify(err));
            if (typeof err.detail === "string") {
                errorMsg = err.detail;
            } else if (Array.isArray(err.detail) && err.detail[0]) {
                const d = err.detail[0];
                errorMsg = d.msg || d.message || JSON.stringify(d);
            } else if (err.detail) {
                errorMsg = JSON.stringify(err.detail);
            }
        } catch (parseErr) {
            console.error("[Stream] Could not parse error response:", parseErr);
        }
        contentElem.innerHTML = `<span style="color:#ef4444;">${escapeHtml(errorMsg)}</span>`;
        return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop(); // Keep partial line in buffer

        for (const line of lines) {
            if (line.startsWith("data: ")) {
                try {
                    const data = JSON.parse(line.replace("data: ", ""));

                    if (data.type === "user_created") {
                        const userMessages = document.querySelectorAll(".user-message .delete-message");
                        if (userMessages.length > 0) {
                            userMessages[userMessages.length - 1].dataset.id = data.user_message_id;
                        }
                    } else if (data.type === "status") {
                        statusText.textContent = data.message;
                    } else if (data.type === "sources") {
                        accumulatedSources = data.sources;
                    } else if (data.type === "token") {
                        if (statusBox && statusBox.parentNode) {
                            clearInterval(timerInterval);
                            statusBox.remove();
                        }
                        accumulatedText += data.content;
                        contentElem.innerHTML = marked.parse(accumulatedText);
                        scrollToBottom();
                    } else if (data.type === "done") {
                        if (statusBox && statusBox.parentNode) {
                            clearInterval(timerInterval);
                            statusBox.remove();
                        }
                        accumulatedText = data.full_content;
                        accumulatedSources = data.sources || [];
                        accumulatedTools = data.tools_used || [];

                        contentElem.innerHTML = marked.parse(accumulatedText);

                        if (accumulatedTools.length > 0) {
                            toolsElem.textContent = `🔧 Used: ${accumulatedTools.join(", ")}`;
                            toolsElem.style.display = "block";
                        }

                        if (accumulatedSources.length > 0) {
                            sourcesElem.innerHTML = `
                                <div class="sources-title">🔎 Sources</div>
                                ${accumulatedSources.map((source) => `
                                    <div class="source">
                                        <a href="${escapeAttribute(source.url)}" target="_blank" rel="noopener noreferrer">
                                            ${escapeHtml(source.title)}
                                        </a>
                                        <p>${escapeHtml(source.snippet || "")}</p>
                                    </div>
                                `).join("")}
                            `;
                            sourcesElem.style.display = "block";
                        }
                        scrollToBottom();
                    } else if (data.type === "persisted") {
                        if (data.assistant_message_id) {
                            deleteBtn.dataset.id = data.assistant_message_id;
                            deleteBtn.style.display = "inline-block";
                        }
                    }
                } catch (err) {
                    console.error("SSE parse error:", err, line);
                }
            }
        }
    }

    await loadChats();
}

// ============================================================
// Export Chat Functionality
// ============================================================

async function exportChat() {
    if (!currentChatId) {
        showToast("Select a conversation to export", "⚠️");
        return;
    }

    try {
        const messages = await getMessages(currentChatId);
        if (messages.length === 0) {
            showToast("No messages to export", "⚠️");
            return;
        }

        let markdownContent = `# ResearchMate Export\n*Exported on ${new Date().toLocaleString()}*\n\n---\n\n`;

        messages.forEach((msg) => {
            const role = msg.role === "user" ? "### 👤 User" : "### 🔬 ResearchMate";
            markdownContent += `${role}\n\n${msg.content}\n\n---\n\n`;
        });

        const blob = new Blob([markdownContent], { type: "text/markdown;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", `ResearchMate_Chat_${currentChatId}.md`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        showToast("Report exported as .md", "📥");
    } catch (err) {
        console.error("Export error:", err);
        showToast("Failed to export chat", "⚠️");
    }
}

// ============================================================
// Helpers
// ============================================================

function copyText(text, btnElement = null) {
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
        if (btnElement) {
            const originalHtml = btnElement.innerHTML;
            btnElement.innerHTML = "✓ Copied";
            btnElement.classList.add("copied");
            setTimeout(() => {
                btnElement.innerHTML = originalHtml;
                btnElement.classList.remove("copied");
            }, 1800);
        }
    }).catch(() => {
        if (btnElement) {
            btnElement.textContent = "Error";
            setTimeout(() => {
                btnElement.innerHTML = "📋 Copy";
            }, 1500);
        }
    });
}

function scrollToBottom() {
    const messagesContainer = document.getElementById("messages");
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// ============================================================
// Event Listeners & Initialization
// ============================================================

document.getElementById("message-form").addEventListener("submit", async function (event) {
    event.preventDefault();
    const input = document.getElementById("message-input");
    const content = input.value.trim();
    if (!content) return;

    input.value = "";
    addUserMessage(content);

    try {
        await streamSendMessage(content);
    } catch (error) {
        console.error("Stream error:", error);
    }
});

document.getElementById("new-chat-button").addEventListener("click", startNewChat);

document.getElementById("theme-toggle")?.addEventListener("click", toggleTheme);
document.getElementById("export-button")?.addEventListener("click", exportChat);

document.getElementById("message-input").addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        document.getElementById("message-form").requestSubmit();
    }
});

const logoutButton = document.getElementById("logout-button");
if (logoutButton) {
    logoutButton.addEventListener("click", () => {
        localStorage.removeItem("access_token");
        window.location.href = "/";
    });
}

document.getElementById("messages").addEventListener("click", async function (event) {
    if (event.target.classList.contains("delete-message")) {
        const messageId = event.target.dataset.id;
        if (!messageId) return;

        const confirmed = await showConfirmDialog({
            title: "Delete Message?",
            message: "Are you sure you want to delete this message from the conversation?",
            confirmLabel: "Delete",
            cancelLabel: "Cancel",
            isDanger: true,
        });
        if (!confirmed) return;

        try {
            await deleteMessage(currentChatId, messageId);
            showToast("Message deleted", "🗑️");
            await openChat(currentChatId);
        } catch (error) {
            console.error(error);
            showToast("Could not delete message", "⚠️");
        }
    }
});

async function apiFetch(url, options = {}) {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "/";
        return;
    }

    const headers = {
        ...(options.headers || {}),
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
    };

    const response = await fetch(url, {
        ...options,
        headers: headers,
    });

    if (response.status === 401) {
        localStorage.removeItem("access_token");
        window.location.href = "/";
        return;
    }

    return response;
}

window.addEventListener("DOMContentLoaded", async function () {
    initTheme();
    try {
        await loadChats();

        if (allChats.length === 0) {
            currentChatId = null;
            showWelcome();
            return;
        }

        if (currentChatId) {
            const chatExists = allChats.some((chat) => chat.id === currentChatId);
            if (chatExists) {
                await openChat(currentChatId);
                return;
            }
        }

        const latestChat = allChats[0];
        await openChat(latestChat.id);
    } catch (error) {
        console.error("Could not load chat history:", error);
    }
});
