/**
 * main.js - Application functionality (initialization moved to init.js)
 */

let viewer = null;
let bridge = null;

/**
 * Disable/enable UI elements during initialization
 */
function toggleUI(enabled) {
    const elements = [
        '#boltType', '#diameter', '#length', '#material',
        '#bottomNut', '#topNut', '#washers',
        '#generateBtn', '#downloadBtn'
    ];
    
    elements.forEach(selector => {
        const element = document.querySelector(selector);
        if (element) {
            element.disabled = !enabled;
        }
    });
    
    // Also disable form submission
    const form = document.getElementById('boltForm');
    if (form) {
        if (enabled) {
            form.classList.remove('disabled');
        } else {
            form.classList.add('disabled');
        }
    }
}

function setupFormListeners() {
    const downloadBtn = document.getElementById('downloadBtn');

    // Initialize execution options based on default bolt type
    updateExecutionOptions();

    // Initialize length options based on default values
    updateLengthOptions();

    // Download button
    downloadBtn.addEventListener('click', () => {
        if (bridge.getIFCData()) {
            downloadIFCFile();
        }
    });

    // Update execution options based on bolt type
    document.getElementById('boltType').addEventListener('change', updateExecutionOptions);

    // Update length options when bolt type, execution, or diameter changes
    document.getElementById('boltType').addEventListener('change', updateLengthOptions);
    document.getElementById('execution').addEventListener('change', updateLengthOptions);
    document.getElementById('diameter').addEventListener('change', updateLengthOptions);

    // Add event listeners for all form inputs to trigger automatic regeneration
    document.getElementById('boltType').addEventListener('change', () => {
        // Debounce to prevent too frequent updates
        debounce(generateBolt, 300)();
    });
    
    document.getElementById('diameter').addEventListener('change', () => {
        debounce(generateBolt, 300)();
    });
    
    document.getElementById('length').addEventListener('change', () => {
        debounce(generateBolt, 300)();
    });
    
    document.getElementById('material').addEventListener('change', () => {
        debounce(generateBolt, 300)();
    });
    
    document.getElementById('bottomNut').addEventListener('change', () => {
        debounce(generateBolt, 300)();
    });
    
    document.getElementById('topNut').addEventListener('change', () => {
        debounce(generateBolt, 300)();
    });
    
    document.getElementById('washers').addEventListener('change', () => {
        debounce(generateBolt, 300)();
    });

    // Mesh selection event
    window.addEventListener('meshSelected', (e) => {
        updatePropertiesPanel(e.detail);
    });
    
    // Enable UI after all listeners are set up
    toggleUI(true);
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

function updateLengthOptions() {
    const boltType = document.getElementById('boltType').value;
    const execution = parseInt(document.getElementById('execution').value || '1');
    const diameter = parseInt(document.getElementById('diameter').value || '0');
    const lengthSelect = document.getElementById('length');

    // Clear current options
    lengthSelect.innerHTML = '';

    // If any required parameter is missing, return
    if (!boltType || !diameter) {
        return;
    }

    // Get available lengths from Python module via Pyodide
    try {
        // Access the Python module through Pyodide by importing gost_data
        const result = pyodide.runPython(`
            import sys
            sys.path.insert(0, '/python')
            import gost_data
            key = ("${boltType}", ${execution}, ${diameter})
            lengths = gost_data.AVAILABLE_LENGTHS.get(key, [])
            sorted(lengths)  # Sort lengths in ascending order
        `);
        
        // Convert Python list to JavaScript array
        const lengthsArray = result.toJs();
        
        if (lengthsArray.length > 0) {
            // Add options to the select element
            lengthsArray.forEach(length => {
                const option = document.createElement('option');
                option.value = length;
                option.textContent = `${length} мм`;
                lengthSelect.appendChild(option);
            });
            
            // Automatically select the smallest length (first option)
            lengthSelect.value = lengthsArray[0];
        } else {
            // If no lengths found for this combination, add a disabled option
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'Нет доступных длин';
            option.disabled = true;
            lengthSelect.appendChild(option);
        }
    } catch (error) {
        console.error('Error getting available lengths:', error);
        
        // Fallback: add a generic error message option
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'Ошибка загрузки длин';
        option.disabled = true;
        lengthSelect.appendChild(option);
    }
}

async function generateBolt() {
    const params = getFormParams();

    if (!validateParams(params)) {
        // Don't show error if some fields are not filled yet
        // This can happen during initial loading or when changing parameters
        return;
    }

    // Check if bridge is initialized
    if (!bridge) {
        showStatus('Ошибка: Приложение не инициализировано. Перезагрузите страницу.', 'error', 5000);
        return;
    }

    // Disable UI during generation
    toggleUI(false);
    
    showStatus(`Генерирую болт: ${params.bolt_type}, М${params.diameter}x${params.length}...`, 'info');

    try {
        const result = await bridge.generateBolt(params);

        if (result.status === 'error') {
            showStatus(`Ошибка: ${result.message}`, 'error', 5000);
            return;
        }

        // Update 3D view preserving current camera orientation
        if (result.meshData) {
            viewer.updateMeshesPreserveView(result.meshData);
        }

        // Enable download
        document.getElementById('downloadBtn').disabled = false;

        showStatus(`Болт ${params.bolt_type}.М${params.diameter}x${params.length} успешно сгенерирован!`, 'success', 3000);
    } catch (error) {
        showStatus(`Ошибка: ${error.message}`, 'error', 5000);
        console.error(error);
    } finally {
        // Re-enable UI after generation is complete
        toggleUI(true);
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

/**
 * Generate default bolt with predefined parameters
 */
async function generateDefaultBolt() {
    // Default parameters for the bolt
    const defaultParams = {
        bolt_type: '1.1',
        execution: 1,
        diameter: 20,
        length: 800,
        material: '09Г2С',
        has_bottom_nut: true,
        has_top_nut: true,
        has_washers: true
    };

    // Update form fields with default values
    document.getElementById('boltType').value = defaultParams.bolt_type;
    document.getElementById('diameter').value = defaultParams.diameter;
    document.getElementById('material').value = defaultParams.material;
    document.getElementById('bottomNut').checked = defaultParams.has_bottom_nut;
    document.getElementById('topNut').checked = defaultParams.has_top_nut;
    document.getElementById('washers').checked = defaultParams.has_washers;

    // Update execution options based on bolt type
    updateExecutionOptions();

    // Update length options based on bolt type, execution, and diameter
    // This will automatically select the smallest available length
    updateLengthOptions();

    // Trigger the change event to generate the bolt with default parameters
    document.getElementById('boltType').dispatchEvent(new Event('change'));
}

// Debounce function to limit frequency of function calls
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Make toggleUI function available globally
window.toggleUI = toggleUI;
