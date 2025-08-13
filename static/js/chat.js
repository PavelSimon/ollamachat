// Chat page JavaScript functionality
let currentChatId = null;
let availableModels = [];
let selectedModel = null;

document.addEventListener('DOMContentLoaded', function () {
    // Load initial data
    loadChats();
    loadModels();

    // Event listeners
    document.getElementById('new-chat-btn').addEventListener('click', createNewChat);
    document.getElementById('send-btn').addEventListener('click', sendMessage);
    document.getElementById('message-input').addEventListener('keypress', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    document.getElementById('model-select').addEventListener('change', function () {
        selectedModel = this.value;
    });
});

function loadChats() {
    return fetch('/api/chats')
        .then(response => response.json())
        .then(data => {
            const chatList = document.getElementById('chat-list');

            if (data.chats && data.chats.length > 0) {
                let html = '';
                data.chats.forEach(chat => {
                    html += `
                        <div class="chat-item" data-chat-id="${chat.id}" onclick="selectChat(${chat.id})">
                            <div class="chat-item-title">${chat.title}</div>
                            <div class="chat-item-preview">${chat.message_count} správ</div>
                        </div>
                    `;
                });
                chatList.innerHTML = html;
            } else {
                chatList.innerHTML = '<div class="loading">Žiadne chaty. Vytvorte nový chat.</div>';
            }
            return data; // Return data for chaining
        })
        .catch(error => {
            console.error('Error loading chats:', error);
            document.getElementById('chat-list').innerHTML = '<div class="loading">Chyba pri načítavaní chatov</div>';
            throw error; // Re-throw for proper error handling
        });
}

function loadModels() {
    fetch('/api/models')
        .then(response => response.json())
        .then(data => {
            const modelSelect = document.getElementById('model-select');

            if (data.models && data.models.length > 0) {
                availableModels = data.models;
                let html = '<option value="">Vyberte model</option>';

                data.models.forEach(model => {
                    html += `<option value="${model.name}">${model.name}</option>`;
                });

                modelSelect.innerHTML = html;

                // Select preferred model or first available
                if (data.models.length > 0) {
                    // Try to find gpt-oss:20b first
                    const preferredModel = data.models.find(model => model.name === 'gpt-oss:20b');
                    if (preferredModel) {
                        selectedModel = preferredModel.name;
                    } else {
                        selectedModel = data.models[0].name;
                    }
                    modelSelect.value = selectedModel;
                }
            } else {
                modelSelect.innerHTML = '<option value="">Žiadne modely dostupné</option>';
            }
        })
        .catch(error => {
            console.error('Error loading models:', error);
            document.getElementById('model-select').innerHTML = '<option value="">Chyba pri načítavaní modelov</option>';
        });
}

function createNewChat() {
    fetch('/api/chats', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
    })
        .then(response => {
            console.log('Response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Chat creation response:', data);
            if (data.id) {
                // Reload chat list and then select the new chat
                loadChats().then(() => {
                    selectChat(data.id);
                });
            } else {
                console.error('No chat ID in response:', data);
                alert('Chyba pri vytváraní chatu: ' + (data.error || 'Neznáma chyba'));
            }
        })
        .catch(error => {
            console.error('Error creating chat:', error);
            alert('Chyba pri vytváraní chatu: ' + error.message);
        });
}

function selectChat(chatId) {
    currentChatId = chatId;

    // Update UI
    document.querySelectorAll('.chat-item').forEach(item => {
        item.classList.remove('active');
    });

    // Find and activate the chat item (with safety check)
    const chatElement = document.querySelector(`[data-chat-id="${chatId}"]`);
    if (chatElement) {
        chatElement.classList.add('active');
    }

    // Show message input
    document.getElementById('message-input-container').style.display = 'block';

    // Load chat messages
    loadChatMessages(chatId);
}

function loadChatMessages(chatId) {
    fetch(`/api/chats/${chatId}`)
        .then(response => response.json())
        .then(data => {
            if (data.id) {
                document.getElementById('current-chat-title').textContent = data.title;
                displayMessages(data.messages);
            } else {
                alert('Chyba pri načítavaní chatu: ' + (data.error || 'Neznáma chyba'));
            }
        })
        .catch(error => {
            console.error('Error loading chat:', error);
            alert('Chyba pri načítavaní chatu');
        });
}

function formatMarkdown(text) {
    if (!text) return '';
    
    // Escape HTML first to prevent XSS
    text = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    
    // Code blocks (must be first to avoid conflicts)
    text = text.replace(/```(\w+)?\n?([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>');
    
    // Inline code
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Tables
    text = formatTables(text);
    
    // Headers (must be before bold/italic)
    text = text.replace(/^### (.*$)/gm, '<h3>$1</h3>');
    text = text.replace(/^## (.*$)/gm, '<h2>$1</h2>');
    text = text.replace(/^# (.*$)/gm, '<h1>$1</h1>');
    
    // Bold and italic
    text = text.replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>');
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Links
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    
    // Lists
    text = formatLists(text);
    
    // Line breaks
    text = text.replace(/\n\n/g, '</p><p>');
    text = text.replace(/\n/g, '<br>');
    
    // Wrap in paragraph if not already wrapped
    if (!text.startsWith('<')) {
        text = '<p>' + text + '</p>';
    }
    
    return text;
}

function formatTables(text) {
    // Match markdown tables
    const tableRegex = /(\|.*\|.*\n\|[-\s|:]+\|.*\n(?:\|.*\|.*\n?)*)/g;
    
    return text.replace(tableRegex, function(match) {
        const lines = match.trim().split('\n');
        if (lines.length < 3) return match; // Need at least header, separator, and one row
        
        const headerLine = lines[0];
        const separatorLine = lines[1];
        const dataLines = lines.slice(2);
        
        // Parse header
        const headers = headerLine.split('|').map(h => h.trim()).filter(h => h);
        
        // Parse alignment from separator
        const alignments = separatorLine.split('|').map(s => {
            s = s.trim();
            if (s.startsWith(':') && s.endsWith(':')) return 'center';
            if (s.endsWith(':')) return 'right';
            return 'left';
        }).filter((_, i) => i < headers.length);
        
        // Build table HTML
        let tableHtml = '<table class="markdown-table"><thead><tr>';
        headers.forEach((header, i) => {
            const align = alignments[i] || 'left';
            tableHtml += `<th style="text-align: ${align}">${header}</th>`;
        });
        tableHtml += '</tr></thead><tbody>';
        
        // Parse data rows
        dataLines.forEach(line => {
            const cells = line.split('|').map(c => c.trim()).filter(c => c);
            if (cells.length > 0) {
                tableHtml += '<tr>';
                cells.forEach((cell, i) => {
                    const align = alignments[i] || 'left';
                    tableHtml += `<td style="text-align: ${align}">${cell}</td>`;
                });
                tableHtml += '</tr>';
            }
        });
        
        tableHtml += '</tbody></table>';
        return tableHtml;
    });
}

function formatLists(text) {
    // Unordered lists
    text = text.replace(/^[\s]*[-*+]\s+(.*)$/gm, '<li>$1</li>');
    text = text.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    
    // Ordered lists
    text = text.replace(/^[\s]*\d+\.\s+(.*)$/gm, '<li>$1</li>');
    
    // Fix nested lists (basic support)
    text = text.replace(/<\/ul>\s*<ul>/g, '');
    text = text.replace(/<\/ol>\s*<ol>/g, '');
    
    return text;
}

function displayMessages(messages) {
    const container = document.getElementById('messages-container');

    if (messages.length === 0) {
        container.innerHTML = '<div class="welcome-message"><h3>Nový chat</h3><p>Začnite konverzáciu napísaním správy.</p></div>';
        return;
    }

    let html = '';
    messages.forEach(message => {
        const isUser = message.is_user;
        const avatar = isUser ? 'U' : 'AI';
        const time = new Date(message.created_at).toLocaleTimeString();

        // Enhanced markdown formatting
        let formattedContent = formatMarkdown(message.content);

        html += `
            <div class="message ${isUser ? 'user' : 'ai'}">
                <div class="message-avatar">${avatar}</div>
                <div class="message-content">
                    ${formattedContent}
                    <div class="message-meta">
                        ${time}${!isUser && message.model_name ? ` • ${message.model_name}` : ''}
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
    container.scrollTop = container.scrollHeight;
}

function sendMessage() {
    const input = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const message = input.value.trim();

    if (!message || !currentChatId || !selectedModel) {
        if (!selectedModel) {
            alert('Vyberte model pre komunikáciu');
        }
        return;
    }

    // Disable input and show loading
    input.disabled = true;
    sendBtn.disabled = true;
    document.querySelector('.send-text').style.display = 'none';
    document.querySelector('.loading-text').style.display = 'inline';

    // Add timeout warning after 30 seconds
    const timeoutWarning = setTimeout(() => {
        document.querySelector('.loading-text').textContent = 'Spracováva sa... (môže trvať dlhšie)';
    }, 30000);

    // Create AbortController for request cancellation
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 150000); // 2.5 minutes timeout

    fetch('/api/messages', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            chat_id: currentChatId,
            message: message,
            model: selectedModel
        }),
        signal: controller.signal
    })
        .then(response => {
            clearTimeout(timeoutId);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.user_message && data.ai_message) {
                // Clear input
                input.value = '';

                // Reload messages
                loadChatMessages(currentChatId);

                // Update chat list (title might have changed)
                loadChats();
            } else {
                console.error('Unexpected response format:', data);
                alert('Chyba pri odosielaní správy: ' + (data.error || 'Neočakávaný formát odpovede'));
            }
        })
        .catch(error => {
            clearTimeout(timeoutId);
            console.error('Error sending message:', error);
            
            let errorMessage = 'Chyba pri odosielaní správy';
            if (error.name === 'AbortError') {
                errorMessage = 'Požiadavka bola zrušená kvôli dlhému času odozvy. Skúste to znovu s kratšou správou.';
            } else if (error.message.includes('Failed to fetch')) {
                errorMessage = 'Chyba pripojenia k serveru. Skontrolujte internetové pripojenie.';
            } else if (error.message.includes('timeout')) {
                errorMessage = 'Požiadavka vypršala. Model možno potrebuje viac času na odpoveď.';
            } else {
                errorMessage += ': ' + error.message;
            }
            
            alert(errorMessage);
        })
        .finally(() => {
            clearTimeout(timeoutWarning);
            clearTimeout(timeoutId);
            
            // Re-enable input
            input.disabled = false;
            sendBtn.disabled = false;
            document.querySelector('.send-text').style.display = 'inline';
            document.querySelector('.loading-text').style.display = 'none';
            document.querySelector('.loading-text').textContent = 'Odosielam...';
            input.focus();
        });
}