// Import các hằng số DOM
import * as dom from './dom.js';

// Import các hàm UI
import {
    updateMobileTopicDisplay,
    closeMobileDropdown,
    showDeleteConfirm,
    addMessage,
    addWelcomeMessage,
    buildConversationElement
} from './ui.js';

// Import các hàm API
import {
    loadChatHistoryApi,
    loadMessagesApi,
    deleteConversationApi,
    renameConversationApi,
    submitChatApi
} from './api.js';

// Import các hàm tính năng
import {
    setupTheme,
    setupSidebarToggle,
    setupSpeechRecognition
} from './features.js';

// --- State Toàn cục ---
let currentThreadId = null;


/* -------------------------------
   Định nghĩa các Hàm Handler Chính
   ------------------------------- */

async function loadChatHistory() {
    try {
        const history = await loadChatHistoryApi();
        dom.chatHistoryContainer.innerHTML = '';
        history.forEach(convo => {
            const el = buildConversationElement(
                convo,
                switchConversation,
                renameConversation,
                deleteConversation
            );
            if (convo.thread_id === currentThreadId) {
                el.querySelector('.chat-history-item').classList.add('active');
            }
            dom.chatHistoryContainer.appendChild(el);
        });
        updateMobileTopicDisplay();
    } catch (error) {
        console.error("Lỗi khi tải lịch sử chat:", error);
    }
}

async function loadMessagesForThread(threadId) {
    dom.chatWindow.innerHTML = '';
    if (!threadId) {
        addWelcomeMessage();
        return;
    }
    try {
        const conversation = await loadMessagesApi(threadId);
        if (conversation && conversation.messages) {
            conversation.messages.forEach(msg => addMessage(msg.content, msg.sender, false));
            dom.chatWindow.scrollTop = dom.chatWindow.scrollHeight;
        } else {
            addWelcomeMessage();
        }
    } catch (error) {
        console.error("Lỗi khi tải tin nhắn:", error);
        addWelcomeMessage();
    }
}

function switchConversation(threadId) {
    currentThreadId = threadId;
    localStorage.setItem('chat_thread_id', threadId);
    loadMessagesForThread(threadId);
    document.querySelectorAll('.chat-history-item').forEach(item => {
        item.classList.toggle('active', item.dataset.threadId === threadId);
    });
}

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
                await renameConversationApi(threadId, newTitle);
            } catch (error) {
                console.error("Lỗi khi đổi tên:", error);
            }
        }
        // Luôn tải lại lịch sử sau khi rename (dù thành công hay thất bại)
        await loadChatHistory();
    };

    input.addEventListener('blur', saveName);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') input.blur();
    });
}

async function deleteConversation(threadId, wrapper) {
    const ok = await showDeleteConfirm('Xóa cuộc trò chuyện này?');
    if (!ok) return;
    try {
        await deleteConversationApi(threadId);
        wrapper.remove();
        if (currentThreadId === threadId) {
            handleNewChat(); // Chuyển về chat mới nếu xóa chat hiện tại
        }
    } catch (err) {
        console.error('Xóa thất bại', err);
        alert('Không thể xóa cuộc trò chuyện.');
    }
}

function handleNewChat() {
    currentThreadId = `thread_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    localStorage.setItem('chat_thread_id', currentThreadId);
    dom.chatWindow.innerHTML = '';
    addWelcomeMessage();
    loadChatHistory(); // Tải lại để thêm mục "New Chat" (nếu cần) hoặc bỏ active
    if (dom.mobileTopicDisplay) {
        dom.mobileTopicDisplay.textContent = "New Chat";
    }
    closeMobileDropdown();
}

async function handleChatSubmit(event) {
    event.preventDefault();
    const userMessage = dom.chatInput.value.trim();
    if (userMessage === '') return;

    if (!currentThreadId) {
        currentThreadId = `thread_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
        localStorage.setItem('chat_thread_id', currentThreadId);
    }

    addMessage(userMessage, 'user');
    dom.chatInput.value = '';
    dom.chatInput.style.height = 'auto'; // Sửa lỗi chiều cao
    dom.sendButton.disabled = true;
    dom.chatInput.disabled = true;

    try {
        const data = await submitChatApi(userMessage, currentThreadId);
        if (data.content) {
            addMessage(data.content, 'assistant');
        } else {
            addMessage(`Lỗi: ${data.error || 'Không nhận được phản hồi'}`, 'assistant');
        }
        
        const existingElement = dom.chatHistoryContainer.querySelector(`.history-item-wrapper[data-thread-id="${currentThreadId}"]`);
        if (!existingElement) {
            await loadChatHistory(); 
        } else {
            dom.chatHistoryContainer.prepend(existingElement);
        }
        switchConversation(currentThreadId); // Đảm bảo luôn active
    } catch (error) {
        console.error('Lỗi khi gửi tin nhắn:', error);
        addMessage('Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại.', 'assistant');
    } finally {
        dom.sendButton.disabled = false;
        dom.chatInput.disabled = false;
        dom.chatInput.focus();
    }
}

/* -------------------------------
   Khởi tạo Ứng dụng
   ------------------------------- */
document.addEventListener('DOMContentLoaded', () => {
    // Thiết lập các tính năng
    setupTheme(dom.themeSwitch, dom.sunIcon, dom.moonIcon);
    setupSidebarToggle(dom.sidebarToggleButton, dom.appLayout);
    setupSpeechRecognition(dom.micButton, dom.chatInput);

    // Gán các sự kiện chính
    dom.chatForm.addEventListener('submit', handleChatSubmit);
    dom.newChatButton.addEventListener('click', handleNewChat);

    dom.chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleChatSubmit(e);
        }
    });
    
    // Sửa lỗi co giãn input
    dom.chatInput.addEventListener('input', () => {
        dom.chatInput.style.height = '24px'; // Reset về chiều cao cơ sở (24px)
        dom.chatInput.style.height = Math.min(dom.chatInput.scrollHeight, 160) + 'px';
    });

    // Sự kiện mobile (từ code cũ)
    dom.chatHistoryContainer.addEventListener('click', function(event) {
        const clickedTopic = event.target.closest('.chat-history-item');
        if (clickedTopic) {
            if (dom.mobileTopicDisplay) {
                dom.mobileTopicDisplay.textContent = clickedTopic.textContent;
            }
            closeMobileDropdown();
        }
    });

    document.addEventListener('click', function(event) {
        const isMobile = window.innerWidth <= 768;
        const isMenuOpen = dom.appLayout.classList.contains('sidebar-collapsed');
        if (isMobile && isMenuOpen) {
            const sidebar = document.querySelector('.sidebar');
            if (sidebar && !sidebar.contains(event.target)) {
                closeMobileDropdown();
            }
        }
    });

    // Tải dữ liệu ban đầu
    currentThreadId = localStorage.getItem('chat_thread_id');
    loadChatHistory();
    loadMessagesForThread(currentThreadId);
});