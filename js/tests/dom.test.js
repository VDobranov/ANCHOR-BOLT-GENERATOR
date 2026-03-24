/**
 * Тесты для dom.js
 */

import {
    getById,
    querySelectorAll,
    querySelector,
    addClass,
    removeClass,
    toggleClass,
    setText,
    setHTML,
    addEventListener,
    removeEventListener
} from '../utils/dom.js';

describe('dom.js', () => {
    beforeEach(() => {
        // Очищаем DOM перед каждым тестом
        document.body.innerHTML =
            '<div id="test">Test</div><div class="item">Item 1</div><div class="item">Item 2</div>';
    });

    describe('getById', () => {
        test('должен возвращать элемент по ID', () => {
            const element = getById('test');
            expect(element).not.toBeNull();
            expect(element.id).toBe('test');
            expect(element.textContent).toBe('Test');
        });

        test('должен возвращать null для несуществующего ID', () => {
            const element = getById('nonexistent');
            expect(element).toBeNull();
        });
    });

    describe('querySelectorAll', () => {
        test('должен возвращать NodeList элементов по селектору', () => {
            const elements = querySelectorAll('.item');
            expect(elements.length).toBe(2);
            expect(elements[0].textContent).toBe('Item 1');
            expect(elements[1].textContent).toBe('Item 2');
        });

        test('должен возвращать пустой NodeList для несуществующего селектора', () => {
            const elements = querySelectorAll('.nonexistent');
            expect(elements.length).toBe(0);
        });
    });

    describe('querySelector', () => {
        test('должен возвращать первый элемент по селектору', () => {
            const element = querySelector('.item');
            expect(element).not.toBeNull();
            expect(element.textContent).toBe('Item 1');
        });

        test('должен возвращать null для несуществующего селектора', () => {
            const element = querySelector('.nonexistent');
            expect(element).toBeNull();
        });
    });

    describe('addClass', () => {
        test('должен добавлять класс элементу', () => {
            const element = getById('test');
            addClass(element, 'new-class');
            expect(element.classList.contains('new-class')).toBe(true);
        });

        test('не должен бросать ошибку для null элемента', () => {
            expect(() => addClass(null, 'class')).not.toThrow();
        });

        test('не должен бросать ошибку для undefined элемента', () => {
            expect(() => addClass(undefined, 'class')).not.toThrow();
        });
    });

    describe('removeClass', () => {
        test('должен удалять класс у элемента', () => {
            const element = getById('test');
            element.classList.add('to-remove');
            removeClass(element, 'to-remove');
            expect(element.classList.contains('to-remove')).toBe(false);
        });

        test('не должен бросать ошибку для null элемента', () => {
            expect(() => removeClass(null, 'class')).not.toThrow();
        });

        test('не должен бросать ошибку для undefined элемента', () => {
            expect(() => removeClass(undefined, 'class')).not.toThrow();
        });
    });

    describe('toggleClass', () => {
        test('должен переключать класс у элемента', () => {
            const element = getById('test');
            toggleClass(element, 'toggle-class');
            expect(element.classList.contains('toggle-class')).toBe(true);

            toggleClass(element, 'toggle-class');
            expect(element.classList.contains('toggle-class')).toBe(false);
        });

        test('не должен бросать ошибку для null элемента', () => {
            expect(() => toggleClass(null, 'class')).not.toThrow();
        });

        test('не должен бросать ошибку для undefined элемента', () => {
            expect(() => toggleClass(undefined, 'class')).not.toThrow();
        });
    });

    describe('setText', () => {
        test('должен устанавливать текст элемента', () => {
            const element = getById('test');
            setText(element, 'New Text');
            expect(element.textContent).toBe('New Text');
        });

        test('не должен бросать ошибку для null элемента', () => {
            expect(() => setText(null, 'text')).not.toThrow();
        });

        test('не должен бросать ошибку для undefined элемента', () => {
            expect(() => setText(undefined, 'text')).not.toThrow();
        });
    });

    describe('setHTML', () => {
        test('должен устанавливать HTML элемента', () => {
            const element = getById('test');
            setHTML(element, '<span>New HTML</span>');
            expect(element.innerHTML).toBe('<span>New HTML</span>');
        });

        test('не должен бросать ошибку для null элемента', () => {
            expect(() => setHTML(null, '<span>html</span>')).not.toThrow();
        });

        test('не должен бросать ошибку для undefined элемента', () => {
            expect(() => setHTML(undefined, '<span>html</span>')).not.toThrow();
        });
    });

    describe('addEventListener', () => {
        test('должен добавлять обработчик события', () => {
            const element = getById('test');
            let clicked = false;
            const handler = () => {
                clicked = true;
            };
            addEventListener(element, 'click', handler);

            element.click();
            expect(clicked).toBe(true);
        });

        test('не должен бросать ошибку для null элемента', () => {
            expect(() => addEventListener(null, 'click', () => {})).not.toThrow();
        });

        test('не должен бросать ошибку для undefined элемента', () => {
            expect(() => addEventListener(undefined, 'click', () => {})).not.toThrow();
        });
    });

    describe('removeEventListener', () => {
        test('должен удалять обработчик события', () => {
            const element = getById('test');
            let callCount = 0;
            const handler = () => {
                callCount++;
            };

            element.addEventListener('click', handler);
            removeEventListener(element, 'click', handler);

            element.click();
            expect(callCount).toBe(0);
        });

        test('не должен бросать ошибку для null элемента', () => {
            expect(() => removeEventListener(null, 'click', () => {})).not.toThrow();
        });

        test('не должен бросать ошибку для undefined элемента', () => {
            expect(() => removeEventListener(undefined, 'click', () => {})).not.toThrow();
        });
    });
});
