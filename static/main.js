document.addEventListener('DOMContentLoaded', function() {
    const sendButton = document.getElementById('send-btn');
    const clearButton = document.getElementById('clear-btn');
    const messageInput = document.getElementById('message-input');
    const functionSelect = document.getElementById('function-select');
    const loadingIndicator = document.getElementById('loading-indicator');
    const errorArea = document.getElementById('error-area');

    sendButton.addEventListener('click', () => sendMessage());

    // Enter to send
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    clearButton.addEventListener('click', clearChat);

    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;

        // display user message and clear input
        displayMessage('user', message);
        messageInput.value = '';
        errorArea.style.display = 'none';

        // determine endpoint
        let url = '/answer';
        switch (functionSelect.value) {
            case 'search': url = '/search'; break;
            case 'kbanswer': url = '/kbanswer'; break;
            case 'answer': url = '/answer'; break;
        }

        // show loading state
        loadingIndicator.style.display = 'inline-block';
        sendButton.disabled = true;
        functionSelect.disabled = true;
        messageInput.disabled = true;

        try {
            const resp = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });

            if (!resp.ok) {
                const text = await resp.text();
                throw new Error(`Server error: ${resp.status} ${text}`);
            }

            const data = await resp.json();
            displayMessage('assistant', data.message || '(no response)');
        } catch (err) {
            console.error('Chat error', err);
            showError('Sorry — something went wrong. Try again.');
            displayMessage('assistant', 'Error: ' + (err.message || 'Unknown error'), true);
        } finally {
            loadingIndicator.style.display = 'none';
            sendButton.disabled = false;
            functionSelect.disabled = false;
            messageInput.disabled = false;
            messageInput.focus();
        }
    }

    function clearChat() {
        const chatContainer = document.getElementById('chat-container');
        chatContainer.innerHTML = '';
        messageInput.focus();
        errorArea.style.display = 'none';
    }

    function showError(msg) {
        errorArea.style.display = 'block';
        errorArea.innerHTML = `<div class="alert alert-danger" role="alert">${msg}</div>`;
    }

    function displayMessage(sender, message, isError=false) {
        const chatContainer = document.getElementById('chat-container');
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');

        const safeHtml = String(message);

        if (sender === 'assistant') {
            messageDiv.classList.add(isError ? 'error-message' : 'assistant-message');
            messageDiv.innerHTML = `<strong>SageBot:</strong> ${safeHtml}`;
        } else {
            messageDiv.classList.add('user-message');
            messageDiv.innerHTML = `<strong>You:</strong> ${safeHtml}`;
        }

        const timestamp = document.createElement('div');
        timestamp.classList.add('timestamp');
        timestamp.innerText = new Date().toLocaleTimeString();
        messageDiv.appendChild(timestamp);

        chatContainer.appendChild(messageDiv);
        // smooth scroll to latest
        chatContainer.scrollTo({ top: chatContainer.scrollHeight, behavior: 'smooth' });
    }
});
