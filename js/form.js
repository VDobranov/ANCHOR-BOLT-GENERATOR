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
            material: document.getElementById('material'),
            bottomNut: document.getElementById('bottomNut'),
            topNut1: document.getElementById('topNut1'),
            topNut2: document.getElementById('topNut2'),
            washers: document.getElementById('washers')
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
        this.updateBottomComponentsAvailability();
        
        this.setupListeners();
    }

    /**
     * Настройка обработчиков событий
     */
    setupListeners() {
        const { boltType, execution, diameter, length, material,
                bottomNut, topNut1, topNut2, washers } = this.elements;

        // Обновление опций исполнения и длины
        boltType.addEventListener('change', () => {
            this.updateExecutionOptions();
            this.updateLengthOptions();
            this.updateBottomComponentsAvailability();
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

        // Опциональные компоненты
        bottomNut.addEventListener('change', () => this.triggerChange());
        topNut1.addEventListener('change', () => this.triggerChange());
        topNut2.addEventListener('change', () => this.triggerChange());
        washers.addEventListener('change', () => this.triggerChange());
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
                    option.textContent = `${l} мм`;
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

        this.updateBottomComponentsAvailability();
    }

    /**
     * Получение доступных длин через Pyodide
     */
    async getAvailableLengths(boltType, execution, diameter) {
        if (!this.pyodide) {
            // Fallback: пустой список если Pyodide недоступен
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
     * Обновление доступности нижних компонентов (гайки/шайбы)
     */
    updateBottomComponentsAvailability() {
        const { boltType, bottomNut, washers } = this.elements;
        const isBoltType2 = boltType.value.startsWith('2.');

        // Нижняя гайка только для типа 2.x
        bottomNut.disabled = !isBoltType2;
        
        // Шайбы доступны для всех типов
        washers.disabled = false;

        // Сброс нижней гайки если тип не 2.x
        if (!isBoltType2) {
            bottomNut.checked = false;
        }
    }

    /**
     * Получение параметров формы
     */
    getParams() {
        const { boltType, execution, diameter, length, material,
                bottomNut, topNut1, topNut2, washers } = this.elements;

        const isBoltType2 = boltType.value.startsWith('2.');

        return {
            bolt_type: boltType.value,
            execution: parseInt(execution.value || '1'),
            diameter: parseInt(diameter.value || '0'),
            length: parseInt(length.value || '0'),
            material: material.value,
            has_bottom_nut: isBoltType2 ? bottomNut.checked : false,
            has_top_nut1: topNut1.checked,
            has_top_nut2: topNut2.checked,
            has_washers: washers.checked
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
        const { boltType, execution, diameter, length, material,
                bottomNut, topNut1, topNut2, washers } = this.elements;

        boltType.value = params.bolt_type || '1.1';
        execution.value = params.execution || '1';
        diameter.value = params.diameter || '20';
        length.value = params.length || '800';
        material.value = params.material || '09Г2С';
        bottomNut.checked = params.has_bottom_nut || false;
        topNut1.checked = params.has_top_nut1 ?? true;
        topNut2.checked = params.has_top_nut2 ?? true;
        washers.checked = params.has_washers ?? true;

        this.updateExecutionOptions();
        this.updateBottomComponentsAvailability();
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
            material: '09Г2С',
            has_bottom_nut: false,
            has_top_nut1: true,
            has_top_nut2: true,
            has_washers: true
        };
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BoltForm;
}
