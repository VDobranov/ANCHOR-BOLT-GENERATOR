/**
 * form.js — Управление формой и валидация параметров
 */

class BoltForm {
    constructor(options = {}) {
        this.onParamsChange = options.onParamsChange || null;
        this.pyodide = options.pyodide || null;
        
        this.elements = {
            boltType: document.getElementById('boltType'),
            execution: document.getElementById('execution'),
            executionGroup: document.getElementById('executionGroup'),
            diameter: document.getElementById('diameter'),
            length: document.getElementById('length'),
            material: document.getElementById('material')
        };
        
        this.debounceTimer = null;
        this.debounceDelay = 300;
    }

    /**
     * Инициализация обработчиков формы
     */
    init() {
        this.updateExecutionOptions();
        this.updateLengthOptions();
        this.setupListeners();
    }

    /**
     * Настройка обработчиков событий
     */
    setupListeners() {
        const { boltType, execution, diameter, length, material } = this.elements;

        // Обновление опций исполнения и длины
        boltType.addEventListener('change', () => {
            this.updateExecutionOptions();
            this.updateLengthOptions();
            this.triggerChange();
        });

        execution.addEventListener('change', () => {
            this.updateLengthOptions();
            this.triggerChange();
        });

        diameter.addEventListener('change', () => {
            this.updateLengthOptions();
            this.triggerChange();
        });

        length.addEventListener('change', () => this.triggerChange());
        material.addEventListener('change', () => this.triggerChange());
    }

    /**
     * Обновление опций исполнения в зависимости от типа болта
     */
    updateExecutionOptions() {
        const { boltType, execution, executionGroup } = this.elements;
        const boltTypeValue = boltType.value;

        if (!boltTypeValue) {
            if (executionGroup) executionGroup.style.display = 'none';
            return;
        }

        // Типы 2.1 и 5 имеют фиксированное исполнение = 1
        if (boltTypeValue === '2.1' || boltTypeValue === '5') {
            execution.value = '1';
            if (executionGroup) executionGroup.style.display = 'none';
        } 
        // Типы 1.1 и 1.2 определяют исполнение по второй цифре
        else if (boltTypeValue === '1.1' || boltTypeValue === '1.2') {
            execution.value = boltTypeValue === '1.1' ? '1' : '2';
            if (executionGroup) executionGroup.style.display = 'none';
        }
    }

    /**
     * Обновление опций длины из Python-модуля gost_data
     */
    async updateLengthOptions() {
        const { boltType, execution, diameter, length } = this.elements;
        
        length.innerHTML = '';

        const type = boltType.value;
        const exec = parseInt(execution.value || '1');
        const diam = parseInt(diameter.value || '0');

        if (!type || !diam) return;

        try {
            const lengths = await this.getAvailableLengths(type, exec, diam);
            
            if (lengths.length > 0) {
                lengths.forEach(l => {
                    const option = document.createElement('option');
                    option.value = l;
                    option.textContent = `${l}`;
                    length.appendChild(option);
                });
                length.value = lengths[0];
            } else {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'Нет доступных длин';
                option.disabled = true;
                length.appendChild(option);
            }
        } catch (error) {
            console.error('Ошибка загрузки длин:', error);
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'Ошибка загрузки длин';
            option.disabled = true;
            length.appendChild(option);
        }
    }

    /**
     * Получение доступных длин через Pyodide
     */
    async getAvailableLengths(boltType, execution, diameter) {
        if (!this.pyodide) {
            return [];
        }

        return this.pyodide.runPython(`
            import sys
            sys.path.insert(0, '/python')
            import gost_data
            key = ("${boltType}", ${execution}, ${diameter})
            lengths = gost_data.AVAILABLE_LENGTHS.get(key, [])
            sorted(lengths)
        `);
    }

    /**
     * Получение параметров формы
     */
    getParams() {
        const { boltType, execution, diameter, length, material } = this.elements;

        return {
            bolt_type: boltType.value,
            execution: parseInt(execution.value || '1'),
            diameter: parseInt(diameter.value || '0'),
            length: parseInt(length.value || '0'),
            material: material.value
        };
    }

    /**
     * Валидация параметров
     */
    validateParams(params) {
        return params.bolt_type &&
               params.execution &&
               params.diameter > 0 &&
               params.length > 0 &&
               params.material;
    }

    /**
     * Установка параметров формы
     */
    setParams(params) {
        const { boltType, execution, diameter, length, material } = this.elements;

        boltType.value = params.bolt_type || '1.1';
        execution.value = params.execution || '1';
        diameter.value = params.diameter || '20';
        length.value = params.length || '800';
        material.value = params.material || '09Г2С';

        this.updateExecutionOptions();
    }

    /**
     * Триггер изменения параметров с debouncing
     */
    triggerChange() {
        if (!this.onParamsChange) return;

        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            const params = this.getParams();
            if (this.validateParams(params)) {
                this.onParamsChange(params);
            }
        }, this.debounceDelay);
    }

    /**
     * Получение значения по умолчанию
     */
    getDefaultParams() {
        return {
            bolt_type: '1.1',
            execution: 1,
            diameter: 20,
            length: 800,
            material: '09Г2С'
        };
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BoltForm;
}
