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
const appLayout = document.querySelector('.app-layout');
const sidebarToggleButton = document.getElementById('sidebar-toggle-button'); 
const toggleSidebarCollapsedButton = document.getElementById('toggle-sidebar-collapsed');
const mobileTopicDisplay = document.querySelector('.mobile-topic-display');

const API_BASE_URL = 'http://127.0.0.1:8000';
let currentThreadId = null;

function updateMobileTopicDisplay() {
    // Chỉ chạy nếu tìm thấy span (trên desktop sẽ không có)
    if (!mobileTopicDisplay) return;

    // Tìm topic đang có class .active
    const activeTopic = chatHistoryList.querySelector('.chat-history-item.active');
    
    if (activeTopic) {
        mobileTopicDisplay.textContent = activeTopic.textContent;
    } else {
        // Nếu không có gì active, mặc định là "New Chat"
        mobileTopicDisplay.textContent = "New Chat";
    }
}

// Đóng menu dropdown responsive
function closeMobileDropdown() {
    if (window.innerWidth <= 768) {
        appLayout.classList.remove('sidebar-collapsed');
    }
}
newChatButton.addEventListener('click', function() {
    if (mobileTopicDisplay) {
        // Cập nhật text thành "New Chat"
        mobileTopicDisplay.textContent = "New Chat";
    }
    closeMobileDropdown(); // Đóng menu
});
chatHistoryContainer.addEventListener('click', function(event) {
    const clickedTopic = event.target.closest('.chat-history-item');
    
    if (clickedTopic) {
        if (mobileTopicDisplay) {
            // Cập nhật text bằng nội dung của topic
            mobileTopicDisplay.textContent = clickedTopic.textContent;
        }
        closeMobileDropdown(); // Đóng menu
    }
});

/* -------------------------------
   Theme helpers
   ------------------------------- */
function updateThemeIcons(theme) {
    if (!sunIcon || !moonIcon) return;
    sunIcon.classList.toggle('active', theme === 'light');
    moonIcon.classList.toggle('active', theme !== 'light');
}

/* -------------------------------
   Custom confirm modal
   ------------------------------- */
function showDeleteConfirm(message) {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';

        const box = document.createElement('div');
        box.className = 'modal-box';
        box.innerHTML = `
            <h3>${message}</h3>
            <div class="modal-buttons">
                <button class="modal-cancel">Hủy</button>
                <button class="modal-delete">Xóa</button>
            </div>
        `;

        overlay.appendChild(box);
        document.body.appendChild(overlay);

        const cancelBtn = box.querySelector('.modal-cancel');
        const deleteBtn = box.querySelector('.modal-delete');

        cancelBtn.onclick = () => {
            overlay.remove();
            resolve(false);
        };
        deleteBtn.onclick = () => {
            overlay.remove();
            resolve(true);
        };

        overlay.onclick = (e) => {
            if (e.target === overlay) {
                overlay.remove();
                resolve(false);
            }
        };
    });
}

/* -------------------------------
   Build a single conversation DOM element
   ------------------------------- */
function buildConversationElement(convo) {
    const wrapper = document.createElement('div');
    wrapper.classList.add('history-item-wrapper');
    wrapper.dataset.threadId = convo.thread_id;

    const anchor = document.createElement('a');
    anchor.href = '#';
    anchor.classList.add('chat-history-item');
    anchor.dataset.threadId = convo.thread_id;

    const titleSpan = document.createElement('span');
    titleSpan.classList.add('history-title');
    titleSpan.textContent = convo.title || 'Cuộc trò chuyện mới';
    anchor.appendChild(titleSpan);

    const optionsBtn = document.createElement('button');
    optionsBtn.type = 'button';
    optionsBtn.classList.add('options-button');
    optionsBtn.innerHTML = '&#8942;'; // ⋮

    const optionsMenu = document.createElement('div');
    optionsMenu.classList.add('options-menu');
    optionsMenu.innerHTML = `
        <button type="button" class="options-action rename-action">Rename</button>
        <button type="button" class="options-action delete-action">Delete</button>
    `;
    optionsMenu.style.display = 'none';

    anchor.addEventListener('click', (e) => {
        e.preventDefault();
        switchConversation(convo.thread_id);
    });

    anchor.addEventListener('dblclick', (e) => {
        e.preventDefault();
        renameConversation(anchor, convo.thread_id);
    });

    optionsBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        document.querySelectorAll('.options-menu').forEach(m => {
            if (m !== optionsMenu) m.style.display = 'none';
        });
        optionsMenu.style.display = optionsMenu.style.display === 'block' ? 'none' : 'block';
    });

    // === DELETE with custom modal ===
    optionsMenu.querySelector('.delete-action').addEventListener('click', async (e) => {
        e.stopPropagation();
        optionsMenu.style.display = 'none';
        const ok = await showDeleteConfirm('Xóa cuộc trò chuyện này?');
        if (!ok) return;
        try {
            const resp = await fetch(`${API_BASE_URL}/history/${convo.thread_id}`, { method: 'DELETE' });
            if (!resp.ok) throw new Error('Delete failed');
            wrapper.remove();
            if (currentThreadId === convo.thread_id) {
                currentThreadId = null;
                localStorage.removeItem('chat_thread_id');
                chatWindow.innerHTML = '';
                addWelcomeMessage();
            }
        } catch (err) {
            console.error('Xóa thất bại', err);
            alert('Không thể xóa cuộc trò chuyện. Vui lòng thử lại.');
        }
    });

    // === Rename from menu ===
    optionsMenu.querySelector('.rename-action').addEventListener('click', (e) => {
        e.stopPropagation();
        optionsMenu.style.display = 'none';
        renameConversation(anchor, convo.thread_id);
    });

    document.addEventListener('click', (e) => {
        if (!optionsMenu.contains(e.target) && e.target !== optionsBtn) {
            optionsMenu.style.display = 'none';
        }
    });

    wrapper.appendChild(anchor);
    wrapper.appendChild(optionsBtn);
    wrapper.appendChild(optionsMenu);
    return wrapper;
}

/* -------------------------------
   Load chat history
   ------------------------------- */
async function loadChatHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/history?_t=${Date.now()}`, { cache: 'no-cache' });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const history = await response.json();

        chatHistoryContainer.innerHTML = '';
        history.forEach(convo => {
            const el = buildConversationElement(convo);
            if (convo.thread_id === currentThreadId) {
                el.querySelector('.chat-history-item').classList.add('active');
            }
            chatHistoryContainer.appendChild(el);
        });
    } catch (error) {
        console.error("Lỗi khi tải lịch sử chat:", error);
    }
}

/* -------------------------------
   Switch conversation
   ------------------------------- */
function switchConversation(threadId) {
    currentThreadId = threadId;
    localStorage.setItem('chat_thread_id', threadId);
    loadMessagesForThread(threadId);
    document.querySelectorAll('.chat-history-item').forEach(item => {
        item.classList.toggle('active', item.dataset.threadId === threadId);
    });
}

/* -------------------------------
   Load messages
   ------------------------------- */
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
            conversation.messages.forEach(msg => addMessage(msg.content, msg.sender, false));
            chatWindow.scrollTop = chatWindow.scrollHeight;
        } else {
            addWelcomeMessage();
        }
    } catch (error) {
        console.error("Lỗi khi tải tin nhắn:", error);
        addWelcomeMessage();
    }
}

/* -------------------------------
   Rename conversation
   ------------------------------- */
function renameConversation(element, threadId) {
    let currentTitle = '';
    const titleSpan = element.querySelector('.history-title');
    if (titleSpan) currentTitle = titleSpan.textContent;
    if (!currentTitle && element.textContent) currentTitle = element.textContent;

    const input = document.createElement('input');
    input.type = 'text';
    input.value = currentTitle;
    input.classList.add('rename-input');

    if (titleSpan) titleSpan.replaceWith(input);
    else element.replaceWith(input);
    input.focus();

    const saveName = async () => {
        const newTitle = input.value.trim();
        if (newTitle && newTitle !== currentTitle) {
            try {
                const res = await fetch(`${API_BASE_URL}/history/${threadId}/rename?_t=${Date.now()}`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ new_title: newTitle }),
                    cache: 'no-cache'
                });
                if (!res.ok) throw new Error('Rename failed');
                await loadChatHistory();
            } catch (error) {
                console.error("Lỗi khi đổi tên:", error);
                await loadChatHistory();
            }
        } else {
            await loadChatHistory();
        }
    };

    input.addEventListener('blur', saveName);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') input.blur();
    });
}

/* -------------------------------
   New Chat
   ------------------------------- */
function handleNewChat() {
    currentThreadId = `thread_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    localStorage.setItem('chat_thread_id', currentThreadId);
    chatWindow.innerHTML = '';
    addWelcomeMessage();
    loadChatHistory();
}

/* -------------------------------
   Chat display helpers
   ------------------------------- */
function addMessage(text, sender, shouldScroll = true) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender);

    const iconElement = document.createElement('div');
    iconElement.classList.add('message-icon');
    iconElement.innerHTML = sender === 'assistant'
        ? '<img src="images/bk.png" alt="Bot">'
        : '<img src="images/user.png" alt="User">';

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

/* -------------------------------
   Handle sending chat
   ------------------------------- */
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
        if (data.content) addMessage(data.content, 'assistant');
        else addMessage(`Lỗi: ${data.error || 'Không nhận được phản hồi'}`, 'assistant');
        
        const existingElementWrapper = document.querySelector(`.history-item-wrapper[data-thread-id="${currentThreadId}"]`);

        if (!existingElementWrapper) {
            await loadChatHistory(); 
        } else {
            if (chatHistoryContainer.firstChild !== existingElementWrapper) {
                chatHistoryContainer.prepend(existingElementWrapper);
            }
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

function setupSidebarToggle() {
    if (!sidebarToggleButton || !appLayout) return;

    // 1. Tải trạng thái đã lưu khi mở trang
    const isCollapsed = localStorage.getItem('sidebar_collapsed') === 'true';
    appLayout.classList.toggle('sidebar-collapsed', isCollapsed);

    // 2. Thêm sự kiện click
    sidebarToggleButton.addEventListener('click', () => {
        appLayout.classList.toggle('sidebar-collapsed');
        // 3. Lưu trạng thái mới vào localStorage
        const isCurrentlyCollapsed = appLayout.classList.contains('sidebar-collapsed');
        localStorage.setItem('sidebar_collapsed', isCurrentlyCollapsed);
    });
}

/* -------------------------------
   Theme setup + Initialization
   ------------------------------- */
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

document.addEventListener('DOMContentLoaded', () => {
    setupTheme();
    setupSidebarToggle();
    chatForm.addEventListener('submit', handleChatSubmit);
    newChatButton.addEventListener('click', handleNewChat);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleChatSubmit(e);
        }
    });
    chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = (chatInput.scrollHeight) + 'px';
    });

    currentThreadId = localStorage.getItem('chat_thread_id');
    loadChatHistory();
    loadMessagesForThread(currentThreadId);
});

document.addEventListener('click', function(event) {
    const isMobile = window.innerWidth <= 768;
    const isMenuOpen = appLayout.classList.contains('sidebar-collapsed');

    if (isMobile && isMenuOpen) {
        const sidebar = document.querySelector('.sidebar');
        if (sidebar && !sidebar.contains(event.target)) {
            closeMobileDropdown();
        }
    }
});

document.addEventListener('DOMContentLoaded', updateMobileTopicDisplay);
