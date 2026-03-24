/**
 * Тесты для status.js
 */

import { StatusManager, statusManager } from '../ui/status.js';
import { STATUS_TYPES } from '../core/constants.js';
import { APP_CONFIG } from '../core/config.js';

describe('status.js', () => {
    beforeEach(() => {
        // Очищаем DOM и создаём элемент статуса
        document.body.innerHTML = '<div id="status"></div>';
    });

    describe('StatusManager', () => {
        let manager;

        beforeEach(() => {
            manager = new StatusManager();
        });

        describe('init', () => {
            test('должен инициализировать statusElement', () => {
                manager.init();
                expect(manager.statusElement).not.toBeNull();
                expect(manager.statusElement.id).toBe('status');
            });
        });

        describe('show', () => {
            test('должен показывать статус с сообщением и типом', () => {
                manager.show('Test message', STATUS_TYPES.SUCCESS);
                const statusEl = document.getElementById('status');

                expect(statusEl.textContent).toBe('Test message');
                expect(statusEl.classList.contains('status-success')).toBe(true);
                expect(statusEl.style.display).toBe('block');
            });

            test('должен использовать INFO по умолчанию', () => {
                manager.show('Test message');
                const statusEl = document.getElementById('status');

                expect(statusEl.classList.contains('status-info')).toBe(true);
            });

            test('должен очищать предыдущие классы статусов', () => {
                const statusEl = document.getElementById('status');
                statusEl.classList.add('status-error');

                manager.show('Test message', STATUS_TYPES.SUCCESS);

                expect(statusEl.classList.contains('status-error')).toBe(false);
                expect(statusEl.classList.contains('status-success')).toBe(true);
            });

            test('должен работать без предварительной инициализации', () => {
                const newManager = new StatusManager();
                newManager.show('Auto-init', STATUS_TYPES.INFO);

                const statusEl = document.getElementById('status');
                expect(statusEl.textContent).toBe('Auto-init');
            });

            test('должен устанавливать таймер для success статуса', (done) => {
                manager.show('Success!', STATUS_TYPES.SUCCESS);

                // Проверяем, что таймер установлен
                expect(manager.timeoutId).toBeDefined();

                // Ждём истечения таймера
                setTimeout(() => {
                    const statusEl = document.getElementById('status');
                    expect(statusEl.style.display).toBe('none');
                    done();
                }, APP_CONFIG.STATUS_DURATION.success + 50);
            });
        });

        describe('hide', () => {
            test('должен скрывать статус', () => {
                manager.show('Test', STATUS_TYPES.INFO);
                manager.hide();

                const statusEl = document.getElementById('status');
                expect(statusEl.style.display).toBe('none');
            });
        });

        describe('clearAutoHide', () => {
            test('должен очищать таймер', () => {
                manager.show('Test', STATUS_TYPES.SUCCESS);
                manager.clearAutoHide();

                const statusEl = document.getElementById('status');
                expect(statusEl.style.display).toBe('block');
            });
        });

        describe('success', () => {
            test('должен показывать success статус', () => {
                manager.success('Operation completed!');

                const statusEl = document.getElementById('status');
                expect(statusEl.textContent).toBe('Operation completed!');
                expect(statusEl.classList.contains('status-success')).toBe(true);
            });
        });

        describe('error', () => {
            test('должен показывать error статус', () => {
                manager.error('Something went wrong!');

                const statusEl = document.getElementById('status');
                expect(statusEl.textContent).toBe('Something went wrong!');
                expect(statusEl.classList.contains('status-error')).toBe(true);
            });
        });

        describe('info', () => {
            test('должен показывать info статус', () => {
                manager.info('Information message');

                const statusEl = document.getElementById('status');
                expect(statusEl.textContent).toBe('Information message');
                expect(statusEl.classList.contains('status-info')).toBe(true);
            });
        });
    });

    describe('statusManager singleton', () => {
        test('должен экспортировать синглтон', () => {
            expect(statusManager).toBeInstanceOf(StatusManager);
        });

        test('должен работать синглтон', () => {
            statusManager.show('Singleton test', STATUS_TYPES.INFO);
            const statusEl = document.getElementById('status');
            expect(statusEl.textContent).toBe('Singleton test');
        });
    });
});
