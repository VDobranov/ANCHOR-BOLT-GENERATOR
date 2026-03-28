# Инструкция по отправке PR в ifc-gherkin-rules

## Шаг 1: Создать форк репозитория

1. Перейти на https://github.com/IFCOpenShell/ifc-gherkin-rules
2. Нажать кнопку "Fork" (справа вверху)
3. Дождаться создания форка в вашем аккаунте

## Шаг 2: Клонировать форк

```bash
cd /path/to/your/workspace
git clone https://github.com/YOUR_USERNAME/ifc-gherkin-rules.git
cd ifc-gherkin-rules
```

## Шаг 3: Применить исправления

Скопируйте исправленный файл из нашего репозитория:

```bash
cp /path/to/ANCHOR-BOLT-GENERATOR/external/ifc-gherkin-rules/features/steps/steps/propertysets_qtys_units.py \
   /path/to/ifc-gherkin-rules/features/steps/steps/propertysets_qtys_units.py
```

Или примените патч:

```bash
cd /path/to/ifc-gherkin-rules
git apply << 'EOF'
diff --git a/features/steps/steps/propertysets_qtys_units.py b/features/steps/steps/propertysets_qtys_units.py
index 77a8da04..f72eaa49 100644
--- a/features/steps/steps/propertysets_qtys_units.py
+++ b/features/steps/steps/propertysets_qtys_units.py
@@ -144,7 +144,13 @@ def establish_accepted_pset_values(name: str, _schema: str, _table: str, propert
     # but unhashable because it's a dict
     def make_obj(s):
         if s:
-            return json.loads(s.replace("'", '"'))
+            # Use ast.literal_eval for Python literals (handles None, True, False correctly)
+            # Fall back to json.loads for compatibility
+            import ast
+            try:
+                return ast.literal_eval(s)
+            except (ValueError, SyntaxError):
+                return json.loads(s.replace("'", '"'))
         else:
             return ''

@@ -408,10 +414,13 @@ def step_impl(context, inst, table, inst_type=None):
             elif prop.is_a('IfcPropertyEnumeratedValue'):
                 values = prop.EnumerationValues
                 if values:
-                    for value in values:
-                        if not value.wrappedValue in accepted_data_type['values']:
-                            yield ValidationOutcome(inst=inst, expected=accepted_data_type['values'],
-                                                    observed=value.wrappedValue, severity=OutcomeSeverity.ERROR)
+                    # Empty values list in template means "any value is accepted"
+                    if accepted_data_type['values']:
+                        for value in values:
+                            if not value.wrappedValue in accepted_data_type['values']:
+                                yield ValidationOutcome(inst=inst, expected=accepted_data_type['values'],
+                                                        observed=value.wrappedValue, severity=OutcomeSeverity.ERROR)
+                    # If accepted_data_type['values'] is empty, any value is valid (no check needed)

             # @todo other properties such as list/bounded/etc.

EOF
```

## Шаг 4: Создать ветку для PR

```bash
git checkout -b fix/pse001-python-literal-parsing
```

## Шаг 5: Закоммитить изменения

```bash
git add features/steps/steps/propertysets_qtys_units.py
git commit -m "fix: Correct PSE001 validation for Python literals and empty enumerations

- Use ast.literal_eval() for parsing pset_definitions.csv (handles None, True, False)
- Skip validation when enumeration values list is empty (means 'any value accepted')
- Fixes false positive errors for Pset_ElementComponentCommon validation"
```

## Шаг 6: Отправить в форк

```bash
git push origin fix/pse001-python-literal-parsing
```

## Шаг 7: Создать Pull Request

1. Перейти в ваш форк на GitHub
2. Нажать "Compare & pull request"
3. Заполнить описание PR (использовать текст из `PSE001_FIX_PR_DESCRIPTION.md`)
4. Нажать "Create pull request"

## Шаблон описания PR

```markdown
## Summary

This PR fixes two bugs in the PSE001 validation rule that caused false positive errors when validating IFC files with `Pset_ElementComponentCommon`.

## Issues Fixed

### Bug 1: CSV parsing error for Python literals

- **Problem:** `json.loads()` failed on Python constants (`None`, `True`, `False`)
- **Fix:** Use `ast.literal_eval()` with JSON fallback

### Bug 2: Empty enumeration values validation

- **Problem:** Empty `values: []` treated as "only empty allowed" instead of "any value"
- **Fix:** Skip validation when `accepted_data_type['values']` is empty

## Testing

All 91 buildingSMART Gherkin validation features now pass:

- 91 features passed, 0 failed, 8 skipped
- 360 scenarios passed, 0 failed, 11 skipped

## Impact

Enables proper validation of:

- `Pset_ElementComponentCommon` with `IfcPropertyEnumeratedValue` properties
- Any Pset with open enumerations (empty `values: []`)
```

## Шаг 8: Дождаться code review

- Отслеживать комментарии от maintainers
- Внести правки при необходимости
- После approval PR будет merged
