// Settings page JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Test connection on page load
    testConnection();
    
    // Load models on page load
    loadModels();
    
    // Load chat management
    loadChatManagement();
    
    // Event listeners
    const testButton = document.getElementById('test-connection');
    if (testButton) {
        testButton.addEventListener('click', testConnection);
    }
    
    const refreshButton = document.getElementById('refresh-models');
    if (refreshButton) {
        refreshButton.addEventListener('click', loadModels);
    }
    
    const selectAllButton = document.getElementById('select-all-chats');
    if (selectAllButton) {
        selectAllButton.addEventListener('click', selectAllChats);
    }
    
    const deselectAllButton = document.getElementById('deselect-all-chats');
    if (deselectAllButton) {
        deselectAllButton.addEventListener('click', deselectAllChats);
    }
    
    const deleteSelectedButton = document.getElementById('delete-selected-chats');
    if (deleteSelectedButton) {
        deleteSelectedButton.addEventListener('click', deleteSelectedChats);
    }
    
    const deleteAllButton = document.getElementById('delete-all-chats');
    if (deleteAllButton) {
        deleteAllButton.addEventListener('click', deleteAllChats);
    }
    
    // Listen for checkbox changes
    document.addEventListener('change', function(e) {
        if (e.target.type === 'checkbox' && e.target.closest('#chat-management')) {
            updateDeleteButton();
        }
    });
});

function testConnection() {
    const statusElement = document.getElementById('connection-status');
    const testButton = document.getElementById('test-connection');
    
    if (!statusElement || !testButton) return;
    
    statusElement.textContent = 'Testuje sa...';
    statusElement.className = 'status-unknown';
    testButton.disabled = true;
    
    fetch('/api/test-connection')
        .then(response => response.json())
        .then(data => {
            if (data.connected) {
                statusElement.textContent = 'Pripojené';
                statusElement.className = 'status-connected';
            } else {
                statusElement.textContent = 'Nepripojené - ' + (data.error || 'Neznáma chyba');
                statusElement.className = 'status-disconnected';
            }
        })
        .catch(error => {
            console.error('Connection test error:', error);
            statusElement.textContent = 'Chyba testovania';
            statusElement.className = 'status-disconnected';
        })
        .finally(() => {
            testButton.disabled = false;
        });
}

function loadModels() {
    const modelsContainer = document.getElementById('models-list');
    const refreshButton = document.getElementById('refresh-models');
    
    if (!modelsContainer || !refreshButton) return;
    
    modelsContainer.innerHTML = '<p>Načítavajú sa modely...</p>';
    refreshButton.disabled = true;
    
    fetch('/api/models')
        .then(response => response.json())
        .then(data => {
            if (data.models && data.models.length > 0) {
                let html = '';
                data.models.forEach(model => {
                    const sizeGB = (model.size / (1024 * 1024 * 1024)).toFixed(2);
                    html += `
                        <div class="model-item">
                            <div>
                                <div class="model-name">${escapeHtml(model.name)}</div>
                                <div class="model-size">${sizeGB} GB</div>
                            </div>
                        </div>
                    `;
                });
                modelsContainer.innerHTML = html;
            } else {
                modelsContainer.innerHTML = '<p>Žiadne modely nie sú dostupné. Skontrolujte pripojenie k serveru.</p>';
            }
        })
        .catch(error => {
            console.error('Models loading error:', error);
            modelsContainer.innerHTML = '<p>Chyba pri načítavaní modelov. Skontrolujte pripojenie k serveru.</p>';
        })
        .finally(() => {
            refreshButton.disabled = false;
        });
}

function loadChatManagement() {
    const chatManagement = document.getElementById('chat-management');
    const totalChatsSpan = document.getElementById('total-chats');
    
    if (!chatManagement) return;
    
    chatManagement.innerHTML = '<div class="loading">Načítavajú sa chaty...</div>';
    
    fetch('/api/chats')
        .then(response => response.json())
        .then(data => {
            if (data.chats && data.chats.length > 0) {
                if (totalChatsSpan) {
                    totalChatsSpan.textContent = data.chats.length;
                }
                let html = '';
                data.chats.forEach(chat => {
                    const date = new Date(chat.created_at).toLocaleDateString('sk-SK');
                    html += `
                        <div class="chat-item-checkbox">
                            <input type="checkbox" id="chat-${chat.id}" value="${chat.id}">
                            <div class="chat-item-info">
                                <div class="chat-item-title">${escapeHtml(chat.title)}</div>
                                <div class="chat-item-date">${date} • ${chat.message_count} správ</div>
                            </div>
                        </div>
                    `;
                });
                chatManagement.innerHTML = html;
                updateDeleteButton();
            } else {
                if (totalChatsSpan) {
                    totalChatsSpan.textContent = '0';
                }
                chatManagement.innerHTML = '<div class="loading">Žiadne chaty na vymazanie.</div>';
            }
        })
        .catch(error => {
            console.error('Error loading chats:', error);
            chatManagement.innerHTML = '<div class="loading">Chyba pri načítavaní chatov.</div>';
        });
}

function updateDeleteButton() {
    const checkboxes = document.querySelectorAll('#chat-management input[type="checkbox"]');
    const checkedBoxes = document.querySelectorAll('#chat-management input[type="checkbox"]:checked');
    const deleteButton = document.getElementById('delete-selected-chats');
    
    if (deleteButton) {
        deleteButton.disabled = checkedBoxes.length === 0;
        deleteButton.textContent = `Vymazať vybrané (${checkedBoxes.length})`;
    }
}

function selectAllChats() {
    const checkboxes = document.querySelectorAll('#chat-management input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.checked = true;
    });
    updateDeleteButton();
}

function deselectAllChats() {
    const checkboxes = document.querySelectorAll('#chat-management input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    updateDeleteButton();
}

function deleteSelectedChats() {
    const checkedBoxes = document.querySelectorAll('#chat-management input[type="checkbox"]:checked');
    const chatIds = Array.from(checkedBoxes).map(cb => cb.value);
    
    if (chatIds.length === 0) return;
    
    if (!confirm(`Naozaj chcete vymazať ${chatIds.length} chatov? Táto akcia sa nedá vrátiť späť.`)) {
        return;
    }
    
    const deleteButton = document.getElementById('delete-selected-chats');
    if (deleteButton) {
        deleteButton.disabled = true;
        deleteButton.textContent = 'Vymazávam...';
    }
    
    fetch('/api/chats/bulk-delete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ chat_ids: chatIds })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            loadChatManagement(); // Reload the chat list
            if (data.failed_deletions && data.failed_deletions.length > 0) {
                alert(`${data.message}\nNepodarilo sa vymazať chaty: ${data.failed_deletions.join(', ')}`);
            } else {
                alert(`Úspešne vymazané ${data.deleted_count} chatov.`);
            }
        } else {
            alert('Chyba pri vymazávaní chatov: ' + (data.error || 'Neznáma chyba'));
        }
    })
    .catch(error => {
        console.error('Error deleting chats:', error);
        alert('Chyba pri vymazávaní chatov: ' + error.message);
    })
    .finally(() => {
        if (deleteButton) {
            deleteButton.disabled = false;
            deleteButton.textContent = 'Vymazať vybrané (0)';
        }
    });
}

function deleteAllChats() {
    if (!confirm('Naozaj chcete vymazať VŠETKY chaty? Táto akcia sa nedá vrátiť späť.')) {
        return;
    }
    
    const deleteButton = document.getElementById('delete-all-chats');
    if (deleteButton) {
        deleteButton.disabled = true;
        deleteButton.textContent = 'Vymazávam...';
    }
    
    fetch('/api/chats/delete-all', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadChatManagement(); // Reload the chat list
            alert(`Úspešne vymazané ${data.deleted_count} chatov.`);
        } else {
            alert('Chyba pri vymazávaní chatov: ' + (data.error || 'Neznáma chyba'));
        }
    })
    .catch(error => {
        console.error('Error deleting all chats:', error);
        alert('Chyba pri vymazávaní chatov');
    })
    .finally(() => {
        if (deleteButton) {
            deleteButton.disabled = false;
            deleteButton.textContent = 'Vymazať všetky chaty';
        }
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}