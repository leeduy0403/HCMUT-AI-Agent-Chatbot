import { API_BASE_URL } from './dom.js';
import * as dom from './dom.js';

// Biến cục bộ để quản lý audio
let currentAudio = null;

export function updateMobileTopicDisplay() {
    if (!dom.mobileTopicDisplay) return;
    const activeTopic = dom.chatHistoryContainer.querySelector('.chat-history-item.active');
    
    if (activeTopic) {
        // Lấy chính xác từ span .history-title bên trong
        const titleSpan = activeTopic.querySelector('.history-title');
        dom.mobileTopicDisplay.textContent = titleSpan ? titleSpan.textContent : activeTopic.textContent;
    } else {
        dom.mobileTopicDisplay.textContent = "New Chat";
    }
}

export function closeMobileDropdown() {
    if (window.innerWidth <= 768) {
        dom.appLayout.classList.remove('sidebar-collapsed');
    }
}

export function showDeleteConfirm(message) {
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

        cancelBtn.onclick = () => { overlay.remove(); resolve(false); };
        deleteBtn.onclick = () => { overlay.remove(); resolve(true); };
        overlay.onclick = (e) => {
            if (e.target === overlay) { overlay.remove(); resolve(false); }
        };
    });
}

export function addMessage(text, sender, scroll = true) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}`;

    let innerHTML = `
        <div class="message-icon">${sender === 'assistant' ? '<img src="images/bk.png">' : '<img src="images/user.png">'}</div>
        <div class="message-text">${text}</div>
    `;

    if (sender === 'assistant') {
        innerHTML += `
            <button class="tts-button" title="Đọc tin nhắn">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                    <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                </svg>
            </button>
        `;
    }

    msgDiv.innerHTML = innerHTML;

    if (sender === 'assistant') {
        const ttsButton = msgDiv.querySelector('.tts-button');
        if (ttsButton) {
            ttsButton.addEventListener('click', async (e) => {
                e.stopPropagation();
                if (currentAudio) {
                    currentAudio.pause();
                    currentAudio = null;
                }
                ttsButton.disabled = true;

                try {
                    const response = await fetch(`${API_BASE_URL}/speak`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ text: text })
                    });
                    if (!response.ok) throw new Error('Không thể tải audio');
                    
                    const blob = await response.blob();
                    const audioUrl = URL.createObjectURL(blob);
                    
                    currentAudio = new Audio(audioUrl);
                    currentAudio.play();
                    currentAudio.onended = () => {
                        ttsButton.disabled = false;
                        URL.revokeObjectURL(audioUrl);
                        currentAudio = null;
                    };
                } catch (error) {
                    console.error("Lỗi khi phát audio:", error);
                    ttsButton.disabled = false;
                }
            });
        }
    }

    dom.chatWindow.appendChild(msgDiv);
    if (scroll) dom.chatWindow.scrollTop = dom.chatWindow.scrollHeight;
}

export function addWelcomeMessage() {
    addMessage("Dạ, em là BK Assistant. Em có thể hỗ trợ Anh/Chị về thông tin tuyển sinh...", 'assistant');
}

export function buildConversationElement(convo, onSwitch, onRename, onDelete) {
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
    optionsBtn.innerHTML = '&#8942;';

    const optionsMenu = document.createElement('div');
    optionsMenu.classList.add('options-menu');
    optionsMenu.innerHTML = `
        <button type="button" class="options-action rename-action">Rename</button>
        <button type="button" class="options-action delete-action">Delete</button>
    `;
    optionsMenu.style.display = 'none';

    // === Gán sự kiện (Callbacks) ===
    anchor.addEventListener('click', (e) => {
        e.preventDefault();
        onSwitch(convo.thread_id);
    });
    anchor.addEventListener('dblclick', (e) => {
        e.preventDefault();
        onRename(anchor, convo.thread_id);
    });

    optionsBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        document.querySelectorAll('.options-menu').forEach(m => {
            if (m !== optionsMenu) m.style.display = 'none';
        });
        optionsMenu.style.display = optionsMenu.style.display === 'block' ? 'none' : 'block';
    });

    optionsMenu.querySelector('.rename-action').addEventListener('click', (e) => {
        e.stopPropagation();
        optionsMenu.style.display = 'none';
        onRename(anchor, convo.thread_id);
    });
    
    optionsMenu.querySelector('.delete-action').addEventListener('click', async (e) => {
        e.stopPropagation();
        optionsMenu.style.display = 'none';
        await onDelete(convo.thread_id, wrapper);
    });

    // Đóng menu khi click ra ngoài
    document.addEventListener('click', (e) => {
        if (!wrapper.contains(e.target)) {
            optionsMenu.style.display = 'none';
        }
    });

    wrapper.appendChild(anchor);
    wrapper.appendChild(optionsBtn);
    wrapper.appendChild(optionsMenu);
    return wrapper;
}