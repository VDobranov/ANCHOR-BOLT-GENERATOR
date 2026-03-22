#!/usr/bin/env python3
"""
test_all_combinations.py — Массовое тестирование всех комбинаций болтов
Упрощённая версия с прямой валидацией через behave
"""

import os
import sys
import csv
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass

# Добавляем python в путь
sys.path.insert(0, str(Path(__file__).parent / "python"))

from data.validation import AVAILABLE_LENGTHS, BOLT_TYPES


@dataclass
class TestResult:
    bolt_type: str
    diameter: int
    length: int
    assembly_class: str
    assembly_mode: str
    geometry_type: str
    features_passed: int
    features_failed: int
    scenarios_passed: int
    scenarios_failed: int
    status: str
    error_message: str = ""


def get_available_lengths(bolt_type: str, diameter: int) -> List[int]:
    """Получить доступные длины для типа и диаметра"""
    type_key = (bolt_type, diameter)
    
    if type_key not in AVAILABLE_LENGTHS:
        return []
    
    lengths = AVAILABLE_LENGTHS[type_key]
    if lengths:
        # Берём минимальную, среднюю и максимальную длину
        if len(lengths) <= 3:
            return list(lengths)
        step = len(lengths) // 3
        return [lengths[0], lengths[step], lengths[-1]]
    return []


def generate_bolt_ifc(
    bolt_type: str, diameter: int, length: int,
    assembly_class: str, assembly_mode: str, geometry_type: str,
    output_path: str
) -> bool:
    """Сгенерировать IFC файл болта"""
    try:
        from main import initialize_base_document, reset_doc_manager
        from instance_factory import InstanceFactory
        
        reset_doc_manager()
        ifc_doc = initialize_base_document('test')
        
        builder = InstanceFactory(ifc_doc, geometry_type=geometry_type)
        builder.create_bolt_assembly(
            bolt_type=bolt_type,
            diameter=diameter,
            length=length,
            material='09Г2С',
            assembly_class=assembly_class,
            assembly_mode=assembly_mode,
            geometry_type=geometry_type
        )
        
        ifc_doc.write(output_path)
        return True
    except Exception as e:
        print(f"  ERROR генерации: {type(e).__name__}: {e}")
        return False


def run_validation(ifc_path: str, rules_path: str) -> Tuple[int, int, int, int, str]:
    """Запустить валидацию buildingSMART через behave"""
    import subprocess
    
    try:
        # Запускаем из директории ifc-gherkin-rules
        rules_dir = str(Path(__file__).parent / "external" / "ifc-gherkin-rules")
        
        cmd = [
            sys.executable, "-m", "behave",
            "--define", f"input={ifc_path}",
            "--tags=-@disabled",
            "--tags=-@IFC2X3",
            "--tags=-@IFC4.3",
            "--tags=-@critical",
            "--format", "progress",
            "features/rules/"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=rules_dir
        )
        
        output = result.stdout + result.stderr
        
        # Отладка: сохраняем вывод в файл
        with open('/tmp/behave_debug.log', 'a') as f:
            f.write(f"\n=== {ifc_path} ===\n")
            f.write(output[:500])  # Первые 500 символов
        
        # Парсим результаты
        features_passed = features_failed = scenarios_passed = scenarios_failed = 0
        
        for line in output.split('\n'):
            if 'features passed' in line or 'features failed' in line:
                parts = line.split(',')
                for part in parts:
                    part = part.strip()
                    if 'features passed' in part:
                        features_passed = int(part.split()[0])
                    elif 'features failed' in part:
                        features_failed = int(part.split()[0])
            
            if 'scenarios passed' in line or 'scenarios failed' in line:
                parts = line.split(',')
                for part in parts:
                    part = part.strip()
                    if 'scenarios passed' in part:
                        scenarios_passed = int(part.split()[0])
                    elif 'scenarios failed' in part:
                        scenarios_failed = int(part.split()[0])
        
        error = ""
        if result.returncode != 0 and features_failed == 0 and features_passed == 0:
            error = "Behave error"
        
        return features_passed, features_failed, scenarios_passed, scenarios_failed, error
        
    except subprocess.TimeoutExpired:
        return 0, 0, 0, 0, "Timeout"
    except Exception as e:
        return 0, 0, 0, 0, str(e)


def run_all_tests(output_dir: str = "test_output") -> List[TestResult]:
    """Запустить все тесты"""
    
    # Параметры
    bolt_types = ["1.1", "1.2", "2.1", "5"]
    diameters = list(range(12, 49, 2))
    assembly_classes = ["IfcMechanicalFastener", "IfcElementAssembly"]
    assembly_modes = ["separate", "unified"]
    geometry_types = ["solid", "brep"]
    
    # Путь к правилам
    rules_path = str(Path(__file__).parent / "external" / "ifc-gherkin-rules" / "features" / "rules")
    
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    total = 0
    passed_count = 0
    
    print("=" * 80)
    print("МАССОВОЕ ТЕСТИРОВАНИЕ ВСЕХ КОМБИНАЦИЙ")
    print("=" * 80)
    
    for bolt_type in bolt_types:
        for diameter in diameters:
            lengths = get_available_lengths(bolt_type, diameter)
            
            if not lengths:
                continue
            
            for length in lengths:
                for assembly_class in assembly_classes:
                    for assembly_mode in assembly_modes:
                        for geometry_type in geometry_types:
                            total += 1
                            
                            filename = f"bolt_{bolt_type}_M{diameter}x{length}_{assembly_class}_{assembly_mode}_{geometry_type}.ifc"
                            ifc_path = str(Path(output_dir).resolve() / filename)  # Абсолютный путь!
                            
                            print(f"\n[{total}] {bolt_type} M{diameter}x{length} | {assembly_mode} | {geometry_type}", end=" ")
                            
                            # Генерация
                            if not generate_bolt_ifc(
                                bolt_type, diameter, length,
                                assembly_class, assembly_mode, geometry_type,
                                ifc_path
                            ):
                                results.append(TestResult(
                                    bolt_type=bolt_type, diameter=diameter, length=length,
                                    assembly_class=assembly_class, assembly_mode=assembly_mode,
                                    geometry_type=geometry_type,
                                    features_passed=0, features_failed=0,
                                    scenarios_passed=0, scenarios_failed=0,
                                    status="ERROR", error_message="Generation failed"
                                ))
                                continue
                            
                            print("→ генерация OK", end=" ")
                            
                            # Валидация
                            fp, ff, sp, sf, error = run_validation(ifc_path, rules_path)
                            
                            status = "PASS" if ff == 0 else "FAIL"
                            if error:
                                status = "ERROR"
                            if status == "PASS":
                                passed_count += 1
                            
                            results.append(TestResult(
                                bolt_type=bolt_type, diameter=diameter, length=length,
                                assembly_class=assembly_class, assembly_mode=assembly_mode,
                                geometry_type=geometry_type,
                                features_passed=fp, features_failed=ff,
                                scenarios_passed=sp, scenarios_failed=sf,
                                status=status, error_message=error
                            ))
                            
                            print(f"→ {fp} passed, {ff} failed | {status}")
    
    return results


def print_summary(results: List[TestResult]):
    """Вывести сводку"""
    print("\n" + "=" * 80)
    print("СВОДКА РЕЗУЛЬТАТОВ")
    print("=" * 80)
    
    total = len(results)
    passed = sum(1 for r in results if r.status == "PASS")
    failed = sum(1 for r in results if r.status == "FAIL")
    errors = sum(1 for r in results if r.status == "ERROR")
    
    print(f"\nВсего тестов: {total}")
    print(f"✅ PASS: {passed} ({100*passed/total:.1f}%)")
    print(f"❌ FAIL: {failed} ({100*failed/total:.1f}%)")
    print(f"⚠️  ERROR: {errors} ({100*errors/total:.1f}%)")
    
    # По типу болта
    print("\n--- По типу болта ---")
    for bt in ["1.1", "1.2", "2.1", "5"]:
        bt_results = [r for r in results if r.bolt_type == bt]
        bt_passed = sum(1 for r in bt_results if r.status == "PASS")
        print(f"  {bt}: {bt_passed}/{len(bt_results)} passed")
    
    # По assembly mode
    print("\n--- По assembly mode ---")
    for am in ["separate", "unified"]:
        am_results = [r for r in results if r.assembly_mode == am]
        am_passed = sum(1 for r in am_results if r.status == "PASS")
        print(f"  {am}: {am_passed}/{len(am_results)} passed")
    
    # По geometry type
    print("\n--- По geometry type ---")
    for gt in ["solid", "brep"]:
        gt_results = [r for r in results if r.geometry_type == gt]
        gt_passed = sum(1 for r in gt_results if r.status == "PASS")
        print(f"  {gt}: {gt_passed}/{len(gt_results)} passed")
    
    # Проваленные
    if failed > 0:
        print("\n--- Проваленные тесты (первые 10) ---")
        for r in results[:10]:
            if r.status == "FAIL":
                print(f"  {r.bolt_type} M{r.diameter}x{r.length} | {r.assembly_mode} | {r.geometry_type}")
                print(f"    Features: {r.features_passed} passed, {r.features_failed} failed")
    
    if errors > 0:
        print("\n--- Ошибки (первые 10) ---")
        for r in results[:10]:
            if r.status == "ERROR":
                print(f"  {r.bolt_type} M{r.diameter}x{r.length} | {r.assembly_mode} | {r.geometry_type}")
                print(f"    Error: {r.error_message}")


def save_results(results: List[TestResult], output_file: str):
    """Сохранить в CSV"""
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'bolt_type', 'diameter', 'length', 'assembly_class',
            'assembly_mode', 'geometry_type', 'status',
            'features_passed', 'features_failed',
            'scenarios_passed', 'scenarios_failed',
            'error_message'
        ])
        
        for r in results:
            writer.writerow([
                r.bolt_type, r.diameter, r.length, r.assembly_class,
                r.assembly_mode, r.geometry_type, r.status,
                r.features_passed, r.features_failed,
                r.scenarios_passed, r.scenarios_failed,
                r.error_message
            ])
    
    print(f"\nРезультаты: {output_file}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Массовое тестирование комбинаций болтов')
    parser.add_argument('--output-dir', default='test_output', help='Директория для IFC')
    parser.add_argument('--results-file', default='test_results.csv', help='CSV файл')
    
    args = parser.parse_args()
    
    results = run_all_tests(args.output_dir)
    print_summary(results)
    save_results(results, args.results_file)
