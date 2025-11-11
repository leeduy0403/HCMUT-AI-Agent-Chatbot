export function setupTheme(themeSwitch, sunIcon, moonIcon) {
    function updateIcons(theme) {
        if (!sunIcon || !moonIcon) return;
        sunIcon.classList.toggle('active', theme === 'light');
        moonIcon.classList.toggle('active', theme !== 'light');
    }
    
    themeSwitch.addEventListener('change', () => {
        const theme = themeSwitch.checked ? 'light' : 'dark';
        document.body.classList.toggle('light-mode', themeSwitch.checked);
        localStorage.setItem('theme', theme);
        updateIcons(theme);
    });

    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.body.classList.toggle('light-mode', savedTheme === 'light');
    themeSwitch.checked = savedTheme === 'light';
    updateIcons(savedTheme);
}

export function setupSidebarToggle(sidebarToggleButton, appLayout) {
    if (!sidebarToggleButton || !appLayout) return;

    const isCollapsed = localStorage.getItem('sidebar_collapsed') === 'true';
    appLayout.classList.toggle('sidebar-collapsed', isCollapsed);

    sidebarToggleButton.addEventListener('click', () => {
        appLayout.classList.toggle('sidebar-collapsed');
        const isCurrentlyCollapsed = appLayout.classList.contains('sidebar-collapsed');
        localStorage.setItem('sidebar_collapsed', isCurrentlyCollapsed);
    });
}

export function setupSpeechRecognition(micButton, chatInput) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        if (micButton) micButton.style.display = 'none';
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'vi-VN';
    let isListening = false;

    if (micButton) {
        micButton.addEventListener('click', () => {
            if (isListening) recognition.stop();
            else recognition.start();
        });
    }

    recognition.onstart = () => {
        isListening = true;
        micButton.classList.add('listening');
        chatInput.setAttribute('placeholder', 'Đang nghe...');
    };

    recognition.onend = () => {
        isListening = false;
        micButton.classList.remove('listening');
        chatInput.setAttribute('placeholder', 'Nhập câu hỏi...');
        chatInput.style.height = 'auto';
        chatInput.style.height = (chatInput.scrollHeight) + 'px';
        chatInput.focus();
    };

    recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
            .map(result => result[0].transcript)
            .join('');
        chatInput.value = transcript;
    };

    recognition.onerror = (event) => {
        console.error("Lỗi nhận diện giọng nói:", event.error);
        micButton.classList.remove('listening');
        if (event.error === 'not-allowed') {
            alert("Vui lòng cấp quyền truy cập micro.");
        }
    };
}