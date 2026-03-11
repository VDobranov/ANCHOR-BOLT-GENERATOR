## Qwen Added Memories
- При изменении Python-модулей в проекте ANCHOR-BOLT-GENERATOR необходимо проверять все JS-файлы на соответствие: js/config.js (PYTHON_MODULES), js/ifcBridge.js (вызовы Python), js/main.js (инициализация), и другие файлы, которые импортируют или вызывают Python-код
