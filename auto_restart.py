#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автоматический перезапуск бота Ашот
Скрипт для автоматического мониторинга и перезапуска бота при сбоях
"""

import subprocess
import time
import sys
import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional

# Настройка логирования с корректной кодировкой UTF-8
def setup_logging():
    """Настройка логирования с поддержкой UTF-8 и эмодзи"""
    # Создаем форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Настраиваем корневой логгер
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Консольный хендлер с UTF-8
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Настраиваем кодировку для Windows
    if sys.platform == 'win32':
        try:
            # Устанавливаем UTF-8 для консоли Windows
            os.system('chcp 65001 >nul 2>&1')
        except:
            pass
    
    # Файловый хендлер с UTF-8
    try:
        file_handler = logging.FileHandler(
            'bot_supervisor.log', 
            mode='a',
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Ошибка создания файла логов: {e}")
    
    logger.addHandler(console_handler)
    return logger

# Инициализируем логгер
logger = setup_logging()

class BotSupervisor:
    """Класс для управления автоматическим перезапуском бота"""
    
    def __init__(self, 
                 bot_script: str = "rar.py",
                 max_restarts_per_hour: int = 10,
                 restart_delay: int = 5,
                 log_file: str = "bot_supervisor.log"):
        """
        Инициализация супервизора
        
        Args:
            bot_script: Путь к скрипту бота
            max_restarts_per_hour: Максимальное количество перезапусков в час
            restart_delay: Задержка между перезапусками в секундах
            log_file: Файл для логирования
        """
        self.bot_script = bot_script
        self.max_restarts_per_hour = max_restarts_per_hour
        self.restart_delay = restart_delay
        self.log_file = log_file
        self.restart_times: List[datetime] = []
        self.bot_process: Optional[subprocess.Popen] = None
        
        # Проверяем существование скрипта бота
        if not os.path.exists(self.bot_script):
            logger.error(f"ОШИБКА: Скрипт бота не найден: {self.bot_script}")
            sys.exit(1)
    
    def get_python_path(self) -> str:
        """Получение пути к Python (предпочтительно из виртуального окружения)"""
        venv_python = os.path.join("venv", "Scripts", "python.exe")
        if os.path.exists(venv_python):
            return os.path.abspath(venv_python)
        
        # Для Linux/Mac
        venv_python_unix = os.path.join("venv", "bin", "python")
        if os.path.exists(venv_python_unix):
            return os.path.abspath(venv_python_unix)
        
        logger.warning("ВНИМАНИЕ: Виртуальное окружение не найдено, используется системный Python")
        return sys.executable
    
    def clear_old_restart_times(self):
        """Очистка старых записей о перезапусках (старше 1 часа)"""
        current_time = datetime.now()
        self.restart_times = [
            restart_time for restart_time in self.restart_times
            if current_time - restart_time < timedelta(hours=1)
        ]
    
    def can_restart(self) -> bool:
        """Проверка возможности перезапуска (не превышен ли лимит)"""
        self.clear_old_restart_times()
        return len(self.restart_times) < self.max_restarts_per_hour
    
    def start_bot(self) -> Optional[subprocess.Popen]:
        """Запуск бота"""
        try:
            python_path = self.get_python_path()
            logger.info(f"ЗАПУСК: Запуск бота: {self.bot_script}")
            logger.info(f"PYTHON: Используется Python: {python_path}")
            
            # Запускаем бота
            process = subprocess.Popen(
                [python_path, self.bot_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                bufsize=1,
                universal_newlines=True
            )
            
            logger.info(f"УСПЕХ: Бот запущен с PID: {process.pid}")
            return process
            
        except Exception as e:
            logger.error(f"ОШИБКА: Ошибка запуска бота: {e}")
            return None
    
    def is_bot_running(self) -> bool:
        """Проверка работает ли бот"""
        if self.bot_process is None:
            return False
        
        # Проверяем статус процесса
        return_code = self.bot_process.poll()
        if return_code is not None:
            logger.warning(f"ЗАВЕРШЕНИЕ: Процесс бота завершился с кодом: {return_code}")
            
            # Читаем последний вывод
            try:
                stdout, stderr = self.bot_process.communicate(timeout=5)
                if stdout:
                    logger.info(f"ВЫВОД: Последний вывод: {stdout.strip()}")
                if stderr:
                    logger.error(f"ОШИБКИ: {stderr.strip()}")
            except subprocess.TimeoutExpired:
                logger.warning("ТАЙМ-АУТ: Не удалось получить вывод процесса")
            except Exception as e:
                logger.error(f"ОШИБКА: Ошибка при чтении вывода процесса: {e}")
            
            return False
        
        return True
    
    def run(self):
        """Основной цикл супервизора"""
        logger.info("СТАРТ: Запуск супервизора бота Ашот")
        logger.info(f"НАСТРОЙКИ: макс. {self.max_restarts_per_hour} перезапусков/час, задержка {self.restart_delay} сек")
        
        try:
            while True:
                try:
                    # Проверяем, работает ли бот
                    if not self.is_bot_running():
                        
                        # Проверяем лимит перезапусков
                        if not self.can_restart():
                            logger.error(f"ЛИМИТ: Превышен лимит перезапусков ({self.max_restarts_per_hour}/час)")
                            logger.info("ОЖИДАНИЕ: Ожидание 1 час перед следующей попыткой...")
                            time.sleep(3600)  # 1 час
                            continue
                        
                        # Добавляем время перезапуска
                        self.restart_times.append(datetime.now())
                        
                        # Ждем перед перезапуском
                        if self.restart_delay > 0:
                            logger.info(f"ЗАДЕРЖКА: Ожидание {self.restart_delay} секунд перед перезапуском...")
                            time.sleep(self.restart_delay)
                        
                        # Запускаем бота
                        self.bot_process = self.start_bot()
                        
                        if self.bot_process is None:
                            logger.error("ОШИБКА: Не удалось запустить бота, повтор через 30 секунд")
                            time.sleep(30)
                            continue
                    
                    # Ждем перед следующей проверкой
                    time.sleep(10)
                    
                except KeyboardInterrupt:
                    logger.info("ОСТАНОВКА: Получен сигнал остановки (Ctrl+C)")
                    break
                except Exception as e:
                    logger.error(f"ОШИБКА: Ошибка в супервизоре: {e}")
                    time.sleep(30)
        
        finally:
            # Завершаем процесс бота при выходе
            if self.bot_process and self.bot_process.poll() is None:
                logger.info("ЗАВЕРШЕНИЕ: Завершение процесса бота...")
                try:
                    self.bot_process.terminate()
                    self.bot_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning("ПРИНУДИТЕЛЬНОЕ: Принудительное завершение процесса бота")
                    self.bot_process.kill()
                except Exception as e:
                    logger.error(f"ОШИБКА: Ошибка при завершении процесса: {e}")

def main():
    """Главная функция"""
    # Настройки по умолчанию
    supervisor = BotSupervisor(
        bot_script="rar.py",
        max_restarts_per_hour=10,
        restart_delay=5
    )
    
    # Запускаем супервизор
    supervisor.run()

if __name__ == "__main__":
    main() 