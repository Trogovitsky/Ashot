@echo off
chcp 65001 > nul
echo ========================================
echo      BOT ЗАПУСК БОТА АШОТ
echo ========================================
echo.

echo АКТИВАЦИЯ: Активация виртуального окружения...
call venv\Scripts\activate.bat

echo ПРОВЕРКА: Проверка зависимостей...
python -c "import telegram; print('OK: python-telegram-bot установлен')"
python -c "import requests; print('OK: requests установлен')"
python -c "import dotenv; print('OK: python-dotenv установлен')"

echo.
echo ЗАПУСК: Запуск бота...
echo Для остановки бота нажмите Ctrl+C
echo.

python rar.py

pause 