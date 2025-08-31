@echo off
chcp 65001 > nul
title Ashot Bot - AutoRestart

echo ========================================
echo      BOT Запуск бота Ашот с авто-рестартом
echo ========================================
echo.

REM Проверка существования виртуального окружения
if not exist "venv\Scripts\python.exe" (
    echo ОШИБКА: Виртуальное окружение не найдено!
    echo    Создайте его командой: python -m venv venv
    echo    И установите зависимости: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Проверка существования файла бота
if not exist "rar.py" (
    echo ОШИБКА: Файл бота rar.py не найден!
    pause
    exit /b 1
)

REM Проверка .env файла
if not exist ".env" (
    echo ОШИБКА: Файл .env не найден!
    echo    Создайте его и добавьте TELEGRAM_TOKEN=ваш_токен
    pause
    exit /b 1
)

echo НАСТРОЙКИ: Настройки по умолчанию:
echo    • Максимум перезапусков в час: 10
echo    • Задержка перед перезапуском: 5 секунд
echo    • Файл логов: bot_supervisor.log
echo.

echo ЗАПУСК: Запуск супервизора бота...
echo    Для остановки нажмите Ctrl+C
echo.

REM Запуск PowerShell скрипта с автоматическим перезапуском
powershell -ExecutionPolicy Bypass -File "auto_restart.ps1"

echo.
echo ЗАВЕРШЕНИЕ: Супервизор остановлен
pause 