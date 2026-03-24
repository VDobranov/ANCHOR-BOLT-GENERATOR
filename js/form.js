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
    async init() {
        this.updateExecutionOptions();

        // Установить диаметр по умолчанию (М20) перед загрузкой опций
        this.elements.diameter.value = '20';

        await this.updateDiameterOptions();
        await this.updateLengthOptions();
        this.setupListeners();
    }

    /**
     * Настройка обработчиков событий
     */
    setupListeners() {
        const { boltType, diameter, length, material } = this.elements;

        // Обновление опций диаметров и длины
        boltType.addEventListener('change', async () => {
            this.updateExecutionOptions();
            await this.updateDiameterOptions();
            await this.updateLengthOptions();
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
     * Обновление опций диаметров в зависимости от типа болта
     */
    async updateDiameterOptions() {
        const { boltType, diameter } = this.elements;
        const boltTypeValue = boltType.value;

        if (!boltTypeValue) return;

        try {
            const diameters = await this.getAvailableDiameters(boltTypeValue);

            const currentValue = parseInt(diameter.value || '0');
            diameter.innerHTML = '';

            if (diameters.length > 0) {
                diameters.forEach((d) => {
                    const option = document.createElement('option');
                    option.value = d;
                    option.textContent = `M${d}`;
                    diameter.appendChild(option);
                });

                // Сохранить текущее значение если доступно, иначе первое
                if (diameters.includes(currentValue)) {
                    diameter.value = currentValue;
                } else {
                    diameter.value = diameters[0];
                }
            }
        } catch (error) {
            console.error('Ошибка загрузки диаметров:', error);
        }
    }

    /**
     * Получение доступных диаметров для типа болта
     */
    async getAvailableDiameters(boltType) {
        if (!this.pyodide) {
            return [];
        }

        return this.pyodide.runPython(`
            import sys
            sys.path.insert(0, '/python')
            import gost_data

            # Получаем диаметры, для которых есть доступные длины с массой
            available_diameters = []
            for d in gost_data.AVAILABLE_DIAMETERS:
                # Проверяем, есть ли длины для этого диаметра и типа
                key = ("${boltType}", d)
                if key in gost_data.AVAILABLE_LENGTHS and len(gost_data.AVAILABLE_LENGTHS[key]) > 0:
                    available_diameters.append(d)

            sorted(set(available_diameters))
        `);
    }

    /**
     * Обновление опций длины из Python-модуля gost_data
     */
    async updateLengthOptions() {
        const { boltType, diameter, length } = this.elements;

        length.innerHTML = '';

        const type = boltType.value;
        const diam = parseInt(diameter.value || '0');

        if (!type || !diam) return;

        try {
            const lengths = await this.getAvailableLengths(type, diam);

            if (lengths.length > 0) {
                lengths.forEach((l) => {
                    const option = document.createElement('option');
                    option.value = l;
                    option.textContent = `${l}`;
                    length.appendChild(option);
                });
                // Всегда устанавливаем 500 мм при смене типа
                length.value = '500';
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
    async getAvailableLengths(boltType, diameter) {
        if (!this.pyodide) {
            return [];
        }

        return this.pyodide.runPython(`
            import sys
            sys.path.insert(0, '/python')
            import gost_data
            key = ("${boltType}", ${diameter})
            lengths = gost_data.AVAILABLE_LENGTHS.get(key, [])
            sorted(lengths)
        `);
    }

    /**
     * Получение параметров формы
     */
    getParams() {
        const { boltType, diameter, length, material } = this.elements;

        return {
            bolt_type: boltType.value,
            diameter: parseInt(diameter.value || '0'),
            length: parseInt(length.value || '0'),
            material: material.value
        };
    }

    /**
     * Валидация параметров
     */
    validateParams(params) {
        return params.bolt_type && params.diameter > 0 && params.length > 0 && params.material;
    }

    /**
     * Установка параметров формы
     */
    setParams(params) {
        const { boltType, diameter, length, material } = this.elements;

        boltType.value = params.bolt_type || '1.1';
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
            diameter: 20,
            length: 800,
            material: '09Г2С'
        };
    }
}

/**
 * Класс для управления настройками экспорта IFC
 */
class IFCExportSettings {
    constructor(onSettingsChange) {
        this.onSettingsChange = onSettingsChange || null;
        this.elements = {
            assemblyClass: document.getElementById('assemblyClass'),
            assemblyMode: document.getElementById('assemblyMode'),
            geometryType: document.getElementById('geometryType')
        };

        // Добавляем обработчики изменений
        this.setupListeners();
    }

    /**
     * Настройка обработчиков событий
     */
    setupListeners() {
        const { assemblyClass, assemblyMode, geometryType } = this.elements;

        // При изменении настроек — перегенерировать болт
        if (assemblyClass) {
            assemblyClass.addEventListener('change', () => this.triggerChange());
        }
        if (assemblyMode) {
            assemblyMode.addEventListener('change', () => this.triggerChange());
        }
        if (geometryType) {
            geometryType.addEventListener('change', () => this.triggerChange());
        }
    }

    /**
     * Триггер изменения настроек
     */
    triggerChange() {
        if (this.onSettingsChange) {
            this.onSettingsChange(this.getSettings());
        }
    }

    /**
     * Получение текущих настроек экспорта
     * @returns {Object} Настройки экспорта
     */
    getSettings() {
        const settings = {
            assemblyClass: this.elements.assemblyClass?.value || 'IfcMechanicalFastener',
            assemblyMode: this.elements.assemblyMode?.value || 'separate',
            geometryType: this.elements.geometryType?.value || 'solid'
        };

        return settings;
    }

    /**
     * Установка настроек экспорта
     * @param {Object} settings - Настройки для установки
     */
    setSettings(settings) {
        if (settings.assemblyClass && this.elements.assemblyClass) {
            this.elements.assemblyClass.value = settings.assemblyClass;
        }
        if (settings.assemblyMode && this.elements.assemblyMode) {
            this.elements.assemblyMode.value = settings.assemblyMode;
        }
        if (settings.geometryType && this.elements.geometryType) {
            this.elements.geometryType.value = settings.geometryType;
        }
    }

    /**
     * Настройки по умолчанию
     * @returns {Object} Настройки по умолчанию
     */
    getDefaultSettings() {
        return {
            assemblyClass: 'IfcMechanicalFastener',
            assemblyMode: 'separate',
            geometryType: 'solid'
        };
    }
}

// ES6 exports
export { BoltForm, IFCExportSettings };

// CommonJS export для обратной совместимости
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { BoltForm, IFCExportSettings };
}
