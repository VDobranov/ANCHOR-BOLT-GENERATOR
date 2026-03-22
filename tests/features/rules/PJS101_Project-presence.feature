@PJS
@industry-practice
@version1
@pilot
Feature: PJS101 - Project presence

    Правило: PJS101 — Наличие проекта
    
    Требование: Модель должна содержать ровно один IfcProject.
    
    Это общепринятая практика, но отсутствие IfcProject не делает
    IFC-файл невалидным. Например, библиотеки типов могут не следовать
    этому правилу.

    Scenario: IfcProject существует
        Given IFC файл с генератором анкерных болтов
        
        Then Должно быть ровно 1 экземпляр(ов) .IfcProject.
