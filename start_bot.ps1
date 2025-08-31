#!/usr/bin/env pwsh

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "      🤖 ЗАПУСК БОТА АШОТ 🌯" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "🔧 Активация виртуального окружения..." -ForegroundColor Green
try {
    & "venv\Scripts\Activate.ps1"
    Write-Host "✅ Виртуальное окружение активировано" -ForegroundColor Green
} catch {
    Write-Host "❌ Ошибка активации виртуального окружения" -ForegroundColor Red
    Write-Host "Создайте виртуальное окружение: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

Write-Host "📦 Проверка зависимостей..." -ForegroundColor Blue
$dependencies = @("telegram", "requests", "dotenv", "bs4")
foreach ($dep in $dependencies) {
    try {
        python -c "import $dep; print('✅ $dep установлен')"
    } catch {
        Write-Host "❌ $dep не установлен" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "🔍 Проверка файла .env..." -ForegroundColor Blue
if (Test-Path ".env") {
    Write-Host "✅ Файл .env найден" -ForegroundColor Green
} else {
    Write-Host "❌ Файл .env не найден!" -ForegroundColor Red
    Write-Host "Создайте файл .env с токенами бота" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🚀 Запуск бота..." -ForegroundColor Magenta
Write-Host "Для остановки бота нажмите Ctrl+C" -ForegroundColor Yellow
Write-Host ""

try {
    python rar.py
} catch {
    Write-Host "❌ Ошибка запуска бота" -ForegroundColor Red
    Write-Host "Проверьте логи и настройки" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Нажмите любую клавишу для выхода..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 