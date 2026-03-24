# Тестирование JavaScript кода

## Обзор

Проект использует **Jest** для тестирования JavaScript кода. Тесты покрывают ключевые модули приложения с покрытием **≥80%**.

## Запуск тестов

```bash
# Запустить все тесты
npm test

# Запустить тесты с отчётом о покрытии
npm run test:coverage

# Запустить тесты в режиме watch (автоматический перезапуск при изменениях)
npm run test:watch
```

## Структура тестов

```
js/tests/
├── setup.js              # Настройка окружения (mock глобальных объектов)
├── constants.test.js     # Тесты констант приложения
├── config.test.js        # Тесты конфигурации
├── helpers.test.js       # Тесты вспомогательных функций
├── dom.test.js           # Тесты DOM утилит
├── status.test.js        # Тесты менеджера статусов
└── validationService.test.js  # Тесты сервиса валидации
```

## Покрытие кода

Тесты покрывают следующие модули:

| Модуль                             | Покрытие |
| ---------------------------------- | -------- |
| `js/core/config.js`                | 100%     |
| `js/core/constants.js`             | 100%     |
| `js/services/validationService.js` | 97%      |
| `js/ui/status.js`                  | 96%      |
| `js/utils/dom.js`                  | 100%     |
| `js/utils/helpers.js`              | 100%     |

**Общее покрытие: 98%**

## Исключённые модули

Следующие модули исключены из проверки покрытия из-за сложности тестирования (требуют mock Pyodide/Three.js):

- `js/form.js` — управление формой
- `js/viewer.js` — 3D визуализация
- `js/ifcBridge.js` — мост Python↔JavaScript
- `js/main.js` — оркестрация приложения
- `js/init.js` — инициализация
- `js/ui.js` — UI утилиты
- `js/config.js` — конфигурация приложения

## Линтинг и форматирование

```bash
# Запустить ESLint
npm run lint

# Запустить ESLint с авто-исправлением
npm run lint:fix

# Запустить Prettier
npm run format

# Проверить форматирование
npm run format:check
```

## CI/CD

Тесты запускаются автоматически в GitHub Actions при каждом push и pull request:

```yaml
js-tests:
    runs-on: ubuntu-latest
    steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-node@v4
          with:
              node-version: '20'
              cache: 'npm'
        - run: npm ci
        - run: npm test
        - run: npm run test:coverage
```

## Написание тестов

### Пример теста

```javascript
import { ValidationService } from '../services/validationService.js';

describe('ValidationService', () => {
    describe('validateBoltType', () => {
        test('должен возвращать valid=true для правильного типа болта', () => {
            expect(ValidationService.validateBoltType('1.1')).toEqual({ valid: true, error: null });
        });

        test('должен возвращать valid=false для пустого типа', () => {
            expect(ValidationService.validateBoltType('')).toEqual({
                valid: false,
                error: 'Тип болта не указан'
            });
        });
    });
});
```

### Mock глобальных объектов

Для тестирования DOM-зависимых модулей используется `js/tests/setup.js`, который предоставляет mock:

- `global.THREE` — mock Three.js
- `global.document` — mock DOM
- `global.window` — mock window
- `global.UI` — mock UI модуля
- `global.APP_CONFIG` — mock конфигурации

## Пре-коммит хуки

Перед каждым коммитом автоматически запускаются:

- **Prettier** — форматирование кода
- **ESLint** — линтинг JavaScript

Для установки pre-commit хуков:

```bash
pip install pre-commit
pre-commit install
```

## Пороги покрытия

В `package.json` заданы минимальные пороги покрытия:

```json
"coverageThreshold": {
  "global": {
    "branches": 80,
    "functions": 80,
    "lines": 80,
    "statements": 80
  }
}
```

При падении ниже порога тесты не пройдут в CI.
