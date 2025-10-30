// --- Create UI references ---
const chatWindow = document.getElementById('chat-window');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');
const newChatButton = document.getElementById('new-chat-button');
const chatHistoryContainer = document.getElementById('chat-history');
const themeSwitch = document.getElementById('theme-switch-checkbox');
const moonIcon = document.getElementById('moon-icon');
const sunIcon = document.getElementById('sun-icon');

const API_BASE_URL = 'http://127.0.0.1:8000';
let currentThreadId = null;

/**
 * Lấy và hiển thị toàn bộ lịch sử chat trên sidebar
 */
async function loadChatHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/history?_t=${Date.now()}`, { cache: 'no-cache' });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const history = await response.json();
        chatHistoryContainer.innerHTML = '';

        history.forEach(convo => {
            const convoElement = document.createElement('a');
            convoElement.href = '#';
            convoElement.classList.add('chat-history-item');
            convoElement.dataset.threadId = convo.thread_id;
            convoElement.textContent = convo.title || 'Cuộc trò chuyện mới';

            if (convo.thread_id === currentThreadId) {
                convoElement.classList.add('active');
            }

            convoElement.addEventListener('click', (e) => {
                e.preventDefault();
                switchConversation(convo.thread_id);
            });

            convoElement.addEventListener('dblclick', () => {
                renameConversation(convoElement, convo.thread_id);
            });

            chatHistoryContainer.appendChild(convoElement);
        });
    } catch (error) {
        console.error("Lỗi khi tải lịch sử chat:", error);
    }
}

/**
 * Chuyển sang một cuộc hội thoại khác
 */
function switchConversation(threadId) {
    currentThreadId = threadId;
    localStorage.setItem('chat_thread_id', threadId);
    loadMessagesForThread(threadId);
    document.querySelectorAll('.chat-history-item').forEach(item => {
        item.classList.toggle('active', item.dataset.threadId === threadId);
    });
}

/**
 * Tải và hiển thị tin nhắn cho một thread_id cụ thể
 */
async function loadMessagesForThread(threadId) {
    chatWindow.innerHTML = '';
    if (!threadId) {
        addWelcomeMessage();
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/history/${threadId}?_t=${Date.now()}`, { cache: 'no-cache' });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const conversation = await response.json();
        if (conversation && conversation.messages) {
            conversation.messages.forEach(msg => {
                addMessage(msg.content, msg.sender, false);
            });
            chatWindow.scrollTop = chatWindow.scrollHeight;
        } else {
            addWelcomeMessage();
        }
    } catch (error) {
        console.error("Lỗi khi tải tin nhắn:", error);
        addWelcomeMessage();
    }
}

/**
 * Đổi tên conversation (double-click)
 */
function renameConversation(element, threadId) {
    const currentTitle = element.textContent;
    const input = document.createElement('input');
    input.type = 'text';
    input.value = currentTitle;
    input.classList.add('rename-input');

    element.replaceWith(input);
    input.focus();

    const saveName = async () => {
        const newTitle = input.value.trim();
        if (newTitle && newTitle !== currentTitle) {
            try {
                await fetch(`${API_BASE_URL}/history/${threadId}/rename?_t=${Date.now()}`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ new_title: newTitle }),
                    cache: 'no-cache'
                });
                await loadChatHistory();
            } catch (error) {
                console.error("Lỗi khi đổi tên:", error);
                input.replaceWith(element);
            }
        } else {
            input.replaceWith(element);
        }
    };

    input.addEventListener('blur', saveName);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') input.blur();
    });
}

/**
 * New Chat: tạo thread mới và refresh sidebar
 */
function handleNewChat() {
    currentThreadId = `thread_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    localStorage.setItem('chat_thread_id', currentThreadId);
    chatWindow.innerHTML = '';
    addWelcomeMessage();
    document.querySelectorAll('.chat-history-item').forEach(item => item.classList.remove('active'));
    loadChatHistory();
}

/**
 * Thêm tin nhắn vào cửa sổ chat
 */
function addMessage(text, sender, shouldScroll = true) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender);

    const iconElement = document.createElement('div');
    iconElement.classList.add('message-icon');

    if (sender === 'assistant') {
        iconElement.innerHTML = '<img src="images/bk.png" alt="Bot">';
    } else {
        iconElement.innerHTML = '<img src="images/user.png" alt="User">';
    }

    const textElement = document.createElement('div');
    textElement.classList.add('message-text');
    textElement.textContent = text;

    messageElement.appendChild(iconElement);
    messageElement.appendChild(textElement);

    chatWindow.appendChild(messageElement);
    if (shouldScroll) chatWindow.scrollTop = chatWindow.scrollHeight;
}

function addWelcomeMessage() {
    addMessage("Dạ, em là BK Assistant. Em có thể hỗ trợ Anh/Chị về thông tin tuyển sinh, học phí, hoặc các khoa của trường. Anh/Chị cần em giúp gì ạ?", 'assistant');
}

/**
 * Gửi chat
 */
async function handleChatSubmit(event) {
    event.preventDefault();

    const userMessage = chatInput.value.trim();
    if (userMessage === '') return;

    if (!currentThreadId) {
        currentThreadId = `thread_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
        localStorage.setItem('chat_thread_id', currentThreadId);
    }

    addMessage(userMessage, 'user');
    chatInput.value = '';
    chatInput.style.height = 'auto';
    sendButton.disabled = true;
    chatInput.disabled = true;

    try {
        const response = await fetch(`${API_BASE_URL}/chat?_t=${Date.now()}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ message: userMessage, thread_id: currentThreadId }),
            cache: 'no-cache'
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();

        if (data.content) {
            addMessage(data.content, 'assistant');
        } else {
            addMessage(`Lỗi: ${data.error || 'Không nhận được phản hồi'}`, 'assistant');
        }

        // --- Nếu topic mới thì thêm ngay vào sidebar ---
        if (!document.querySelector(`[data-thread-id="${currentThreadId}"]`)) {
            const convoElement = document.createElement('a');
            convoElement.href = '#';
            convoElement.classList.add('chat-history-item', 'active');
            convoElement.dataset.threadId = data.thread_id || currentThreadId;
            convoElement.textContent = data.title || 'Cuộc trò chuyện mới';

            convoElement.addEventListener('click', (e) => {
                e.preventDefault();
                switchConversation(convoElement.dataset.threadId);
            });
            convoElement.addEventListener('dblclick', () => {
                renameConversation(convoElement, convoElement.dataset.threadId);
            });

            document.querySelectorAll('.chat-history-item').forEach(item => item.classList.remove('active'));
            chatHistoryContainer.prepend(convoElement);
        } else {
            await loadChatHistory();
        }

        switchConversation(currentThreadId);

    } catch (error) {
        console.error('Lỗi khi gửi tin nhắn:', error);
        addMessage('Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại.', 'assistant');
    } finally {
        sendButton.disabled = false;
        chatInput.disabled = false;
        chatInput.focus();
    }
}

/**
 * Theme logic
 */
function setupTheme() {
    themeSwitch.addEventListener('change', () => {
        const theme = themeSwitch.checked ? 'light' : 'dark';
        document.body.classList.toggle('light-mode', themeSwitch.checked);
        localStorage.setItem('theme', theme);
        updateThemeIcons(theme);
    });

    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.body.classList.toggle('light-mode', savedTheme === 'light');
    themeSwitch.checked = savedTheme === 'light';
    updateThemeIcons(savedTheme);
}

function updateThemeIcons(theme) {
    const sunIcon = document.getElementById('sun-icon');
    const moonIcon = document.getElementById('moon-icon');
    if (!sunIcon || !moonIcon) return;
    sunIcon.classList.toggle('active', theme === 'light');
    moonIcon.classList.toggle('active', theme !== 'light');
}

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    setupTheme();

    chatForm.addEventListener('submit', handleChatSubmit);
    newChatButton.addEventListener('click', handleNewChat);
    chatInput.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleChatSubmit(e); }});
    chatInput.addEventListener('input', () => { chatInput.style.height = 'auto'; chatInput.style.height = (chatInput.scrollHeight) + 'px'; });

    currentThreadId = localStorage.getItem('chat_thread_id');
    loadChatHistory();
    loadMessagesForThread(currentThreadId);
});
