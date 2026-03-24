/**
 * Тесты для helpers.js
 */

import {
    formatNumber,
    roundTo,
    isDefined,
    isEmpty,
    deepClone,
    getISODate,
    sleep,
    debounce,
    throttle
} from '../utils/helpers.js';

describe('helpers', () => {
    describe('formatNumber', () => {
        test('должен форматировать число с разделителями', () => {
            expect(formatNumber(1000)).toBe('1 000');
            expect(formatNumber(1000000)).toBe('1 000 000');
            expect(formatNumber(1234567)).toBe('1 234 567');
        });

        test('должен возвращать строку для однозначных чисел', () => {
            expect(formatNumber(5)).toBe('5');
            expect(formatNumber(99)).toBe('99');
        });
    });

    describe('roundTo', () => {
        test('должен округлять до 2 знаков по умолчанию', () => {
            expect(roundTo(3.14159)).toBe(3.14);
            expect(roundTo(2.71828)).toBe(2.72);
        });

        test('должен округлять до указанного количества знаков', () => {
            expect(roundTo(3.14159, 3)).toBe(3.142);
            expect(roundTo(3.14159, 1)).toBe(3.1);
            expect(roundTo(3.14159, 0)).toBe(3);
        });
    });

    describe('isDefined', () => {
        test('должен возвращать true для определённых значений', () => {
            expect(isDefined(0)).toBe(true);
            expect(isDefined('')).toBe(true);
            expect(isDefined(false)).toBe(true);
            expect(isDefined({})).toBe(true);
            expect(isDefined([])).toBe(true);
        });

        test('должен возвращать false для null и undefined', () => {
            expect(isDefined(null)).toBe(false);
            expect(isDefined(undefined)).toBe(false);
        });
    });

    describe('isEmpty', () => {
        test('должен возвращать true для пустых значений', () => {
            expect(isEmpty([])).toBe(true);
            expect(isEmpty({})).toBe(true);
            expect(isEmpty('')).toBe(true);
            expect(isEmpty(null)).toBe(true);
            expect(isEmpty(undefined)).toBe(true);
            expect(isEmpty(0)).toBe(true);
            expect(isEmpty(false)).toBe(true);
        });

        test('должен возвращать false для непустых значений', () => {
            expect(isEmpty([1])).toBe(false);
            expect(isEmpty({ a: 1 })).toBe(false);
            expect(isEmpty('abc')).toBe(false);
            expect(isEmpty(1)).toBe(false);
            expect(isEmpty(true)).toBe(false);
        });
    });

    describe('deepClone', () => {
        test('должен глубоко клонировать объект', () => {
            const original = { a: 1, b: { c: 2 } };
            const clone = deepClone(original);

            expect(clone).toEqual(original);
            expect(clone).not.toBe(original);
            expect(clone.b).not.toBe(original.b);

            clone.b.c = 999;
            expect(original.b.c).toBe(2);
        });

        test('должен глубоко клонировать массив', () => {
            const original = [1, [2, 3], { a: 4 }];
            const clone = deepClone(original);

            expect(clone).toEqual(original);
            expect(clone).not.toBe(original);

            clone[1][0] = 999;
            expect(original[1][0]).toBe(2);
        });
    });

    describe('getISODate', () => {
        test('должен возвращать дату в формате ISO', () => {
            const date = getISODate();
            expect(typeof date).toBe('string');
            expect(date).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z$/);
        });

        test('должен возвращать текущую дату', () => {
            const before = new Date().toISOString();
            const result = getISODate();
            const after = new Date().toISOString();

            expect(result >= before).toBe(true);
            expect(result <= after).toBe(true);
        });
    });

    describe('sleep', () => {
        test('должен ждать указанное время', async () => {
            const start = Date.now();
            await sleep(100);
            const end = Date.now();

            expect(end - start).toBeGreaterThanOrEqual(90);
        });

        test('должен возвращать Promise', () => {
            const result = sleep(10);
            expect(result).toBeInstanceOf(Promise);
        });
    });

    describe('debounce', () => {
        test('должен задерживать вызов функции', (done) => {
            let callCount = 0;
            const fn = () => callCount++;
            const debounced = debounce(fn, 50);

            debounced();
            debounced();
            debounced();

            expect(callCount).toBe(0);

            setTimeout(() => {
                expect(callCount).toBe(1);
                done();
            }, 100);
        });

        test('должен сбрасывать таймер при повторных вызовах', (done) => {
            let callCount = 0;
            const fn = () => callCount++;
            const debounced = debounce(fn, 50);

            debounced();

            setTimeout(() => {
                debounced();
            }, 25);

            setTimeout(() => {
                expect(callCount).toBe(1);
                done();
            }, 100);
        });

        test('должен передавать аргументы в функцию', (done) => {
            let lastArg = null;
            const fn = (arg) => {
                lastArg = arg;
            };
            const debounced = debounce(fn, 50);

            debounced('test-value');

            setTimeout(() => {
                expect(lastArg).toBe('test-value');
                done();
            }, 100);
        });
    });

    describe('throttle', () => {
        test('должен ограничивать частоту вызовов функции', (done) => {
            let callCount = 0;
            const fn = () => callCount++;
            const throttled = throttle(fn, 100);

            throttled();
            throttled();
            throttled();

            expect(callCount).toBe(1);

            setTimeout(() => {
                throttled();
                expect(callCount).toBe(2);
                done();
            }, 150);
        });

        test('должен передавать контекст и аргументы', (done) => {
            let receivedArgs = null;
            const fn = function (...args) {
                receivedArgs = args;
            };
            const throttled = throttle(fn, 100);

            throttled('arg1', 'arg2');

            setTimeout(() => {
                expect(receivedArgs).toEqual(['arg1', 'arg2']);
                done();
            }, 150);
        });

        test('должен ждать указанный лимит перед следующим вызовом', (done) => {
            let callCount = 0;
            const fn = () => callCount++;
            const throttled = throttle(fn, 50);

            throttled();
            expect(callCount).toBe(1);

            setTimeout(() => {
                throttled();
                expect(callCount).toBe(1); // Ещё рано
            }, 25);

            setTimeout(() => {
                throttled();
                expect(callCount).toBe(2); // Теперь можно
                done();
            }, 75);
        });
    });
});
