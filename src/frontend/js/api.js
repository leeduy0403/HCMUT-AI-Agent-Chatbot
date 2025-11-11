import { API_BASE_URL } from './dom.js';

export async function loadChatHistoryApi() {
    const response = await fetch(`${API_BASE_URL}/history?_t=${Date.now()}`, { cache: 'no-cache' });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
}

export async function loadMessagesApi(threadId) {
    const response = await fetch(`${API_BASE_URL}/history/${threadId}?_t=${Date.now()}`, { cache: 'no-cache' });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
}

export async function deleteConversationApi(threadId) {
    const resp = await fetch(`${API_BASE_URL}/history/${threadId}`, { method: 'DELETE' });
    if (!resp.ok) throw new Error('Delete failed');
    return await resp.json();
}

export async function renameConversationApi(threadId, newTitle) {
    const res = await fetch(`${API_BASE_URL}/history/${threadId}/rename?_t=${Date.now()}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ new_title: newTitle }),
        cache: 'no-cache'
    });
    if (!res.ok) throw new Error('Rename failed');
    return await res.json();
}

export async function submitChatApi(message, threadId) {
    const response = await fetch(`${API_BASE_URL}/chat?_t=${Date.now()}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ message: message, thread_id: threadId }),
        cache: 'no-cache'
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
}