/**
 * main.js - Application functionality (initialization moved to init.js)
 */

let viewer = null;
let bridge = null;

function setupFormListeners() {
    const form = document.getElementById('boltForm');
    const generateBtn = document.getElementById('generateBtn');
    const downloadBtn = document.getElementById('downloadBtn');

    // Initialize execution options based on default bolt type
    updateExecutionOptions();

    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await generateBolt();
    });

    // Download button
    downloadBtn.addEventListener('click', () => {
        if (bridge.getIFCData()) {
            downloadIFCFile();
        }
    });

    // Update execution options based on bolt type
    document.getElementById('boltType').addEventListener('change', updateExecutionOptions);

    // Mesh selection event
    window.addEventListener('meshSelected', (e) => {
        updatePropertiesPanel(e.detail);
    });
}

function updateExecutionOptions() {
    const boltType = document.getElementById('boltType').value;
    const executionSelect = document.getElementById('execution');
    const executionGroup = document.getElementById('executionGroup');

    if (!boltType) {
        // No type selected, hide execution group
        if (executionGroup) executionGroup.style.display = 'none';
        return;
    }

    if (boltType === '2.1' || boltType === '5') {
        // These types have fixed execution = 1
        executionSelect.value = '1';
        if (executionGroup) executionGroup.style.display = 'none';
    } else if (boltType === '1.1' || boltType === '1.2') {
        // These types have execution determined by second digit
        // For 1.1 execution is 1, for 1.2 execution is 2
        executionSelect.value = boltType === '1.1' ? '1' : '2';
        if (executionGroup) executionGroup.style.display = 'none';
    }
}

async function generateBolt() {
    const params = getFormParams();

    if (!validateParams(params)) {
        showStatus('Пожалуйста, заполните все поля', 'error', 5000);
        return;
    }

    // Check if bridge is initialized
    if (!bridge) {
        showStatus('Ошибка: Приложение не инициализировано. Перезагрузите страницу.', 'error', 5000);
        return;
    }

    const generateBtn = document.getElementById('generateBtn');
    const originalText = generateBtn.textContent;
    generateBtn.disabled = true;
    generateBtn.innerHTML = '<span class="spinner"></span> Генерирую...';

    showStatus('Генерирую болт...', 'info');

    try {
        const result = await bridge.generateBolt(params);

        if (result.status === 'error') {
            showStatus(`Ошибка: ${result.message}`, 'error', 5000);
            return;
        }

        // Update 3D view
        if (result.meshData) {
            viewer.updateMeshes(result.meshData);
        }

        // Enable download
        document.getElementById('downloadBtn').disabled = false;

        showStatus('Болт успешно сгенерирован!', 'success', 3000);
    } catch (error) {
        showStatus(`Ошибка: ${error.message}`, 'error', 5000);
        console.error(error);
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = originalText;
    }
}

function getFormParams() {
    return {
        bolt_type: document.getElementById('boltType').value,
        execution: parseInt(document.getElementById('execution').value || '1'),
        diameter: parseInt(document.getElementById('diameter').value || '0'),
        length: parseInt(document.getElementById('length').value || '0'),
        material: document.getElementById('material').value,
        has_bottom_nut: document.getElementById('bottomNut').checked,
        has_top_nut: document.getElementById('topNut').checked,
        has_washers: document.getElementById('washers').checked
    };
}

function validateParams(params) {
    return params.bolt_type &&
           params.execution &&
           params.diameter > 0 &&
           params.length > 0 &&
           params.material;
}

function downloadIFCFile() {
    const ifcData = bridge.getIFCData();
    if (!ifcData) return;

    const params = getFormParams();
    const filename = `bolt_${params.bolt_type}_M${params.diameter}x${params.length}.ifc`;

    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(ifcData));
    element.setAttribute('download', filename);
    element.style.display = 'none';

    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);

    showStatus(`Файл ${filename} скачан`, 'success', 3000);
}

function updatePropertiesPanel(meshItem) {
    const panel = document.getElementById('propertiesContent');

    if (!meshItem) {
        panel.innerHTML = '<p class="placeholder">Выберите элемент в 3D сцене</p>';
        return;
    }

    let html = `
        <div class="property-item">
            <span class="property-key">Имя:</span>
            <span class="property-value">${meshItem.name}</span>
        </div>
        <div class="property-item">
            <span class="property-key">ID:</span>
            <span class="property-value">${meshItem.id}</span>
        </div>
    `;

    if (meshItem.metadata) {
        Object.entries(meshItem.metadata).forEach(([key, value]) => {
            html += `
                <div class="property-item">
                    <span class="property-key">${key}:</span>
                    <span class="property-value">${value}</span>
                </div>
            `;
        });
    }

    panel.innerHTML = html;
}

function showStatus(message, type = 'info', duration = 0) {
    const statusEl = document.getElementById('statusMessage');
    statusEl.textContent = message;
    statusEl.className = `status-message show ${type}`;

    if (duration > 0) {
        setTimeout(() => {
            statusEl.classList.remove('show');
        }, duration);
    }
}
