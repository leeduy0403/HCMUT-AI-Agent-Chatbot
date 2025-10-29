// --- Create UI ---

const chatWindow = document.getElementById('chat-window');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');
const themeSwitch = document.getElementById('theme-switch-checkbox');
const moonIcon = document.getElementById('moon-icon');
const sunIcon = document.getElementById('sun-icon');


const API_URL = 'http://127.0.0.1:8000/chat';


const thread_id = `thread_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;


chatForm.addEventListener('submit', handleChatSubmit);


chatInput.addEventListener('keydown', (event) => {
    // Gửi tin nhắn nếu nhấn Enter (và không nhấn Shift)
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault(); // Ngăn xuống dòng
        handleChatSubmit(event);
    }
});


chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto'; // Reset chiều cao
    chatInput.style.height = (chatInput.scrollHeight) + 'px'; // Đặt chiều cao mới
});

// 1. Logic khi thay đổi công tắc
themeSwitch.addEventListener('change', () => {
    let theme;
    if (themeSwitch.checked) {
        // Nếu được check (SÁNG)
        document.body.classList.add('light-mode');
        theme = 'light';
        localStorage.setItem('theme', theme);
    } else {
        // Nếu không check (TỐI)
        document.body.classList.remove('light-mode');
        theme = 'dark';
        localStorage.setItem('theme', theme);
    }
    updateThemeIcons(theme); // Gọi hàm cập nhật icon
});

// 2. Logic khi tải trang
document.addEventListener('DOMContentLoaded', () => {
    // Tải chủ đề đã lưu (mặc định là 'dark')
    const savedTheme = localStorage.getItem('theme') || 'dark';
    
    if (savedTheme === 'light') {
        document.body.classList.add('light-mode');
        themeSwitch.checked = true; // Cập nhật trạng thái switch
    } else {
        document.body.classList.remove('light-mode');
        themeSwitch.checked = false; // Cập nhật trạng thái switch
    }
    
    updateThemeIcons(savedTheme); // Cập nhật trạng thái icon
});


/**
 * Hàm chính xử lý việc gửi tin nhắn
 */
async function handleChatSubmit(event) {
    event.preventDefault(); 

    const userMessage = chatInput.value.trim();
    if (userMessage === '') return;

    // Add the user's message to the chat window
    addMessage(userMessage, 'user');

    // Clear the input field and reset height
    chatInput.value = '';
    chatInput.style.height = 'auto';
    
    // Disable the form
    sendButton.disabled = true;
    chatInput.disabled = true;

    try {
        // 5. Send to FastAPI server
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: userMessage,
                thread_id: thread_id 
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // 6. Add the assistant's response
        if (data.content) {
            addMessage(data.content, 'assistant');
        } else if (data.error) {
            addMessage(`Error: ${data.error}`, 'assistant');
        }

    } catch (error) {
        console.error('Error sending message:', error);
        addMessage('Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại.', 'assistant');
    } finally {
        // Re-enable the form
        sendButton.disabled = false;
        chatInput.disabled = false;
        chatInput.focus();
    }
}


function addMessage(text, sender) {
    // Tạo thẻ div .message
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender);

    // Tạo icon
    const iconElement = document.createElement('div');
    iconElement.classList.add('message-icon');
    
    // Đặt nội dung icon (BK cho bot, You cho user)
    if (sender === 'assistant') {
        iconElement.innerHTML = '<img src="images/bk.png" alt="Bot">';
    } else {
        // Chèn avatar của User
        iconElement.innerHTML = '<img src="images/user.png" alt="User">';
    }
    
    // Tạo thẻ div .message-text
    const textElement = document.createElement('div');
    textElement.classList.add('message-text');
    textElement.textContent = text; // Chuyển text thành nội dung

    // Gắn icon và text vào messageElement
    messageElement.appendChild(iconElement);
    messageElement.appendChild(textElement);

    // Gắn messageElement vào cửa sổ chat
    chatWindow.appendChild(messageElement);


    chatWindow.scrollTop = chatWindow.scrollHeight;
}

document.addEventListener('DOMContentLoaded', () => {
    const initialMessage = "Dạ, em là BK Assistant. Em có thể hỗ trợ Anh/Chị về thông tin tuyển sinh, học phí, hoặc các khoa của trường. Anh/Chị cần em giúp gì ạ?";
    addMessage(initialMessage, 'assistant');
});