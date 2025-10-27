// --- JavaScript Logic ---

// 1. Get references to the HTML elements
const chatWindow = document.getElementById('chat-window');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');

// 2. Define the API endpoint
// IMPORTANT: Update this to your deployed URL when you go live!
const API_URL = 'http://127.0.0.1:8000/chat';

// 3. Create a unique thread_id for this conversation session
// This is crucial for the agent to remember the history
const thread_id = `thread_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

// 4. Handle form submission
chatForm.addEventListener('submit', async (event) => {
    event.preventDefault(); // Prevent the page from reloading

    const userMessage = chatInput.value.trim();
    if (userMessage === '') return;

    // Add the user's message to the chat window
    addMessage(userMessage, 'user');

    // Clear the input field
    chatInput.value = '';
    
    // Disable the form while waiting for a response
    sendButton.disabled = true;
    chatInput.disabled = true;

    try {
        // 5. Send the message and thread_id to the FastAPI server
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

        // 6. Add the assistant's response to the chat window
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
});

// 7. Helper function to add a message to the chat window
function addMessage(text, sender) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender);
    messageElement.textContent = text;
    chatWindow.appendChild(messageElement);

    // Auto-scroll to the latest message
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

// 8. Add the initial greeting from the assistant when the page loads
document.addEventListener('DOMContentLoaded', () => {
    const initialMessage = "Dạ, em là BK Assistant. Em có thể hỗ trợ Anh/Chị về thông tin tuyển sinh, học phí, hoặc các khoa của trường. Anh/Chị cần em giúp gì ạ?";
    addMessage(initialMessage, 'assistant');
});