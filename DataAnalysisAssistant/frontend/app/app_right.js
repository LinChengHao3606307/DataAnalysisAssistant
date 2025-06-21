// Chat message buffers
const messageBuffers = {}; // Message ID to content mapping
const lastSubboxes = {}; // Track last subbox for each message

// Chat form submission
document.getElementById("chat-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const input = document.getElementById("user-input");
    const message = input.value.trim();

    if (message) {
        window.ws.send(JSON.stringify({
            type: "chat-user-message",
            content: message
        }));
        input.value = "";
        // Auto-reset textarea height
        input.style.height = 'auto';
        input.style.height = (input.scrollHeight) + 'px';
    }
});

// Input box auto-resize
const userInput = document.getElementById("user-input");
const submitBtn = document.getElementById("submitUserInputBtn");

userInput.style.height = 'auto';
submitBtn.style.height = (userInput.scrollHeight) + 'px';

userInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
    submitBtn.style.height = 'auto';
    submitBtn.style.height = (this.scrollHeight) + 'px';
});

// Chat message handling
function createMessageElement(msgId, isBot) {
    const msgElement = document.createElement("div");
    msgElement.className = `message ${isBot ? 'bot' : 'user'}`;
    msgElement.id = `msg-${msgId}`;

    const contentSpan = document.createElement("span");
    contentSpan.className = 'content';

    if (isBot) {
        const botLabel = document.createElement("span");
        botLabel.className = 'bot-label';
        botLabel.textContent = "BOT: ";
        msgElement.appendChild(botLabel);
    }

    msgElement.appendChild(contentSpan);
    document.getElementById("chat-box").appendChild(msgElement);

    return msgElement;
}

function handleChatStart(msg, isBot) {
    const msgElement = createMessageElement(msg.msg_id, isBot);
    messageBuffers[msg.msg_id] = "";
    lastSubboxes[msg.msg_id] = null;
}

function handleChatChunk(msg, isBot) {
    if (messageBuffers[msg.msg_id] === undefined) return;

    messageBuffers[msg.msg_id] += msg.content;

    let targetElement;
    if (lastSubboxes[msg.msg_id]) {
        targetElement = document.querySelector(`#msg-${msg.msg_id}-${lastSubboxes[msg.msg_id]} .subbox-content`);
    } else {
        targetElement = document.querySelector(`#msg-${msg.msg_id} .content`);
    }

    if (targetElement) {
        const strAttr = targetElement.closest('.subbox')?.getAttribute('atb_str') || 'markdown';

        switch(strAttr) {
            case "raw":
                targetElement.textContent = messageBuffers[msg.msg_id];
                targetElement.style.whiteSpace = 'pre-wrap';
                break;
            case "code":
                targetElement.innerHTML = `<pre>${messageBuffers[msg.msg_id]}</pre>`;
                break;
            case "markdown":
            default:
                targetElement.innerHTML = marked.parse(messageBuffers[msg.msg_id]);
                targetElement.style.whiteSpace = 'normal';
                break;
        }
    }
}

function handleChatDone(msgId) {
    if (messageBuffers[msgId]) {
        document.querySelector(`#msg-${msgId}`).classList.add('completed');
        delete messageBuffers[msgId];
        delete lastSubboxes[msgId];
    }
}

function handleSubboxStart(msg) {
    const parentMsg = document.querySelector(`#msg-${msg.msg_id}`);
    if (!parentMsg) {
        console.error("Parent message not found for subbox");
        return;
    }

    const subboxId = Date.now();
    const subbox = document.createElement("div");
    subbox.className = "subbox";
    subbox.id = `msg-${msg.msg_id}-${subboxId}`;
    subbox.setAttribute('atb_str', msg.atb_str || 'markdown');

    subbox.innerHTML = `
        <div class="subbox-header">${msg.subbox_name || 'Subbox'}</div>
        <div class="subbox-content"></div>
    `;

    if (msg.subbox_color) {
        subbox.style.setProperty('--subbox-bg-color', msg.subbox_color);
    }
    if (msg.text_color) {
        subbox.style.setProperty('--subbox-text-color', msg.text_color);
    }

    parentMsg.appendChild(subbox);
    lastSubboxes[msg.msg_id] = subboxId;
    messageBuffers[msg.msg_id] = "";
}

function handleSubboxEnd(msgId) {
    if (lastSubboxes[msgId]) {
        lastSubboxes[msgId] = null;
        messageBuffers[msgId] = "";
    }
}

// Event listener for chat messages
window.addEventListener('chat-event', (e) => {
    const msg = e.detail;
    console.log("left_main_handler_reached ! ! !")
    console.log(msg.type)
    switch(msg.type) {
        case "chat-chatbot-start":
            handleChatStart(msg, true);
            break;

        case "chat-chatbot-chunk":
            handleChatChunk(msg, true);
            break;

        case "chat-chatbot-done":
            handleChatDone(msg.msg_id);
            break;

        case "chat-chatbot-subbox-start":
            handleSubboxStart(msg);
            break;

        case "chat-user-subbox-start":
            handleSubboxStart(msg);
            break;

        case "chat-chatbot-subbox-end":
            handleSubboxEnd(msg.msg_id);
            break;

        case "chat-user-subbox-end":
            handleSubboxEnd(msg.msg_id);
            break;

        case "chat-user-start":
            handleChatStart(msg, false);
            break;

        case "chat-user-chunk":
            handleChatChunk(msg, false);
            break;

        case "chat-user-done":
            handleChatDone(msg.msg_id);
            break;

        default:
            console.warn("Unknown chat message type:", msg.type);
    }

    // Auto-scroll to bottom
    const chatBox = document.getElementById("chat-box");
    chatBox.scrollTop = chatBox.scrollHeight;
});

// Initialize marked.js for markdown rendering
marked.setOptions({
    breaks: true,
    gfm: true,
    highlight: function(code, lang) {
        if (window.hljs) {
            const language = hljs.getLanguage(lang) ? lang : 'plaintext';
            return hljs.highlight(code, { language }).value;
        }
        return code;
    }
});

// WebSocket error handling
window.ws.onerror = (error) => {
    console.error("WebSocket error:", error);
    const chatBox = document.getElementById("chat-box");
    const errorMsg = document.createElement("div");
    errorMsg.className = "message error";
    errorMsg.textContent = "Connection error occurred. Please refresh the page.";
    chatBox.appendChild(errorMsg);
    chatBox.scrollTop = chatBox.scrollHeight;
};