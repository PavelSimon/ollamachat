// Settings page JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Test connection on page load
    testConnection();
    
    // Load models on page load
    loadModels();
    
    // Test connection button
    const testButton = document.getElementById('test-connection');
    if (testButton) {
        testButton.addEventListener('click', testConnection);
    }
    
    // Refresh models button
    const refreshButton = document.getElementById('refresh-models');
    if (refreshButton) {
        refreshButton.addEventListener('click', loadModels);
    }
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

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}