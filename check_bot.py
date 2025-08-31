import requests
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
BOT_API_URL = f"https://api.telegram.org/bot{TOKEN}"

def check_bot_status():
    """Проверка статуса бота"""
    response = requests.get(f"{BOT_API_URL}/getMe")
    if response.status_code == 200:
        print("✅ Бот доступен")
        bot_info = response.json()
        print(f"Имя бота: {bot_info['result']['first_name']}")
        print(f"Username: @{bot_info['result']['username']}")
    else:
        print("❌ Ошибка при проверке бота:", response.text)
    return response.status_code == 200

def delete_webhook():
    """Удаление webhook"""
    response = requests.get(f"{BOT_API_URL}/deleteWebhook")
    if response.status_code == 200:
        print("✅ Webhook удален")
        return True
    else:
        print("❌ Ошибка при удалении webhook:", response.text)
        return False

def get_webhook_info():
    """Получение информации о webhook"""
    response = requests.get(f"{BOT_API_URL}/getWebhookInfo")
    if response.status_code == 200:
        webhook_info = response.json()['result']
        print("Информация о webhook:")
        print(f"URL: {webhook_info.get('url', 'Не установлен')}")
        print(f"Pending updates: {webhook_info.get('pending_update_count', 0)}")
        if webhook_info.get('last_error_message'):
            print(f"Последняя ошибка: {webhook_info['last_error_message']}")
    else:
        print("❌ Ошибка при получении информации о webhook:", response.text)

if __name__ == "__main__":
    print("🔍 Проверка статуса бота...")
    check_bot_status()
    
    print("\n📡 Информация о webhook:")
    get_webhook_info()
    
    print("\n🧹 Удаление webhook...")
    delete_webhook()
    
    print("\n✨ Готово! Теперь можно запустить бота.") 