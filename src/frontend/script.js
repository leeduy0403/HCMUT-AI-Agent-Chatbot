// --- Create UI ---

const chatWindow = document.getElementById('chat-window');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');


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
        iconElement.textContent = 'BK';
    } else {
        iconElement.textContent = 'You';
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