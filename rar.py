import logging
import re
import os
import requests
import json
import asyncio
import time
from io import BytesIO
from typing import Optional, Tuple
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import yt_dlp
import tempfile

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константы API
YAGPT_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
YANDEX_ART_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/imageGenerationAsync"
ZAYCEV_API_URL = "https://zaycev.net/search.html"
FOLDER_ID = os.getenv("YAGPT_FOLDER_ID")
IAM_TOKEN = os.getenv("YAGPT_IAM_TOKEN")
MODEL_NAME = "yandexgpt-lite"
HITMOTOP_URL = "https://rus.hitmotop.com"
VK_API_URL = "https://api.vk.com/method"
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3"

# API ключи
VK_ACCESS_TOKEN = os.getenv("VK_ACCESS_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Базовый промт для YandexGPT
base_prompt = (
    "Ты — Ашот, продавец шаурмы. Общаешься на русском сленге, как брат. Ты работаешь в шаурмичной. "
    "Отвечай кратко и по делу. Не говори, что ты ИИ. Если тебя спрашивают не о шаурме, отвечай с юмором, но старайся вернуть разговор к заказу. твой хозяин тимофий 1 и чапаев 2 "
    "У тебя есть меню: шаурма в сырном (250 руб), шаурма обычная (240 руб), гигант XXL (500 руб), люля (240 руб), курица гриль (390 руб), курица гриль в лаваше (400 руб), "
    "чебурек (80 руб), пирожок с картошкой (50 руб), самса (70 руб), лепешка (45 руб), напитки: кола (120 руб), махито (100-110 руб), кофе 3в1 (50 руб), латте (150 руб), капучино (145 руб), чай (45 руб)."
    "твоя история -  Я — Ашот, молодой и энергичный мужчина с большой мечтой открыть своё дело. Я всегда любил вкусную еду, особенно шаурму, которую часто покупал на улицах нашего города. Но однажды я задумался: почему бы не сделать шаурму лучше, вкуснее и доступнее для всех?"
    "Собрав немного денег, я арендовал небольшое помещение на оживлённой улице и открыл свою шаурмечную под названием «Ашотова Шаурма». Я тщательно выбирал свежие ингредиенты — ароматное мясо, хрустящие овощи, нежный лаваш и особенный соус по своему рецепту. Я сам освоил искусство приготовления, чтобы каждая шаурма была сочной и аппетитной."
    "Сначала было сложно — конкуренция большая, и люди не сразу замечали новое место. Но я не сдавался: улыбался каждому посетителю, был вежлив и даже устраивал маленькие акции — «вторая шаурма в подарок» или «скидка для студентов». Постепенно о моей шаурме заговорили, и к «Ашотовой Шаурме» стали выстраиваться очереди."
    "Со временем я расширил меню, добавил чай и напитки, а потом открыл ещё одну точку в другом районе города. Моя шаурма стала любимой не только у местных жителей, но и у туристов."
    "Так я не только осуществил свою мечту, но и принес радость вкусной еды многим людям, доказав, что упорство и любовь к своему делу — залог успеха."
)

# Цены и названия позиций
PRICES = {
    "в сырном": 250,
    "две в сырном": 500,
    "в обычном": 240,
    "две в обычном": 480,
    "гигант xxl": 500,
    "люля": 240,
    "две люля": 480,
    "курица гриль": 390,
    "курица гриль в лаваше": 400,
    "чебурек": 80,
    "пирожок с картошкой": 50,
    "самса": 70,
    "лепешка": 45,
    "колу": 120,
    "махито клубничный": 100,
    "махито оригинальный": 100,
    "махито виноград": 110,
    "кофе 3 в 1": 50,
    "латте": 150,
    "капучино": 145,
    "чай зелёный": 45,
    "чай чёрный": 45
}

DISPLAY_NAMES = {
    "в сырном": "Шаурма в сырном",
    "две в сырном": "Две шаурмы в сырном",
    "в обычном": "Шаурма в обычном",
    "две в обычном": "Две шаурмы в обычном",
    "гигант xxl": "Гигант XXL",
    "люля": "Люля-кебаб",
    "две люля": "Два люля-кебаба",
    "курица гриль": "Курица гриль",
    "курица гриль в лаваше": "Курица гриль в лаваше",
    "чебурек": "Чебурек",
    "пирожок с картошкой": "Пирожок с картошкой",
    "самса": "Самса",
    "лепешка": "Лепешка",
    "колу": "Колу",
    "махито клубничный": "Махито клубничный",
    "махито оригинальный": "Махито оригинальный",
    "махито виноград": "Махито виноград",
    "кофе 3 в 1": "Кофе 3 в 1",
    "латте": "Латте",
    "капучино": "Капучино",
    "чай зелёный": "Чай зелёный",
    "чай чёрный": "Чай чёрный"
}

SYNONYMS = {
    "сырном": "в сырном",
    "сырная": "в сырном",
    "сырной": "в сырном",
    "сырный": "в сырном",
    "обычном": "в обычном",
    "обычная": "в обычном",
    "обычной": "в обычном",
    "обычный": "в обычном",
    "гигант": "гигант xxl",
    "гиганта": "гигант xxl",
    "большая": "гигант xxl",
    "люлякебаб": "люля",
    "люля-кебаб": "люля",
    "люли": "люля",
    "гриль": "курица гриль",
    "курин": "курица гриль",
    "курицу": "курица гриль",
    "куриц": "курица гриль",
    "курочк": "курица гриль",
    "чебурека": "чебурек",
    "чебурек": "чебурек",
    "чебуреки": "чебурек",
    "пирожок": "пирожок с картошкой",
    "пирожки": "пирожок с картошкой",
    "пирожка": "пирожок с картошкой",
    "самсу": "самса",
    "самсы": "самса",
    "лепешку": "лепешка",
    "лепешки": "лепешка",
    "лаваш": "лепешка",
    "лаваша": "лепешка",
    "кола": "колу",
    "кока-кола": "колу",
    "пепси": "колу",
    "мохито": "махито оригинальный",
    "мохита": "махито оригинальный",
    "мохито клубничн": "махито клубничный",
    "мохито виноград": "махито виноград",
    "кофе": "кофе 3 в 1",
    "кофей": "кофе 3 в 1",
    "кофя": "кофе 3 в 1",
    "капуччино": "капучино",
    "капучино": "капучино",
    "латте": "латте",
    "чаек": "чай чёрный",
    "зеленый": "чай зелёный",
    "черный": "чай чёрный",
    "две": "2",
    "два": "2",
    "двойн": "2",
    "пару": "2",
    "один": "1",
    "одну": "1",
    "одна": "1",
    "мне": "мне",
    "хочу": "мне",
    "дай": "мне",
    "дайте": "мне",
    "можно": "мне"
}

# Система работ и уровней
JOBS = {
    "Мама дай в долг": {"level": 0, "salary": 50, "command": ["мама дай в долг", "мама мне в долг"]},
    "Промоутер": {"level": 1, "salary": 100, "command": "возьмите пожалуйста листочек"},
    "Расклейщик объявлений": {"level": 2, "salary": 150, "command": "брат наклеил только половину"},
    "Уборщица": {"level": 3, "salary": 200, "command": "я еду"},
    "Таксист": {"level": 4, "salary": 250, "command": "брат я выезжаю"},
    "Официант": {"level": 5, "salary": 500, "command": "что закажите"},
    "Менеджер": {"level": 6, "salary": 700, "command": "брат отчет готов"},
    "Темщик": {"level": 7, "salary": 1500, "command": "пойду на темку"}
}

# Требования для уровней (сколько всего нужно заработать)
LEVEL_REQUIREMENTS = {
    1: 500,     # Уровень 1: 500 руб
    2: 1500,    # Уровень 2: 1500 руб
    3: 3000,    # Уровень 3: 3000 руб
    4: 5000,    # Уровень 4: 5000 руб
    5: 8000,    # Уровень 5: 8000 руб
    6: 12000,   # Уровень 6: 12000 руб
    7: 20000,   # Уровень 7: 20000 руб
    8: 30000,   # Уровень 8: 30000 руб
    9: 50000,   # Уровень 9: 50000 руб
    10: 100000  # Уровень 10: 100000 руб
}

# ==================== СИСТЕМА СОХРАНЕНИЯ ДАННЫХ ==================== #

# Название файла для сохранения данных
USER_DATA_FILE = "user_data.json"

def save_user_data():
    """Сохраняет данные пользователей в JSON файл"""
    print(f"🔍 [DEBUG] Вызвана функция save_user_data()")
    print(f"🔍 [DEBUG] Текущая директория: {os.getcwd()}")
    print(f"🔍 [DEBUG] Файл для сохранения: {USER_DATA_FILE}")
    
    data = {
        "user_balances": user_balances,
        "user_levels": user_levels,
        "user_total_earned": user_total_earned,
        "last_work_time": last_work_time
    }
    
    print(f"🔍 [DEBUG] Данные для сохранения: {data}")
    
    try:
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"🔍 [DEBUG] Файл успешно записан!")
        logger.info("✅ Данные пользователей сохранены в user_data.json")
        
        # Проверяем, что файл действительно создался
        if os.path.exists(USER_DATA_FILE):
            size = os.path.getsize(USER_DATA_FILE)
            print(f"🔍 [DEBUG] Файл создан, размер: {size} байт")
        else:
            print(f"🔍 [DEBUG] ОШИБКА: Файл не найден после записи!")
            
    except Exception as e:
        print(f"🔍 [DEBUG] Исключение при сохранении: {e}")
        logger.error(f"❌ Ошибка сохранения данных: {e}")

def load_user_data():
    """Загружает данные пользователей из JSON файла"""
    global user_balances, user_levels, user_total_earned, last_work_time
    
    try:
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Преобразуем строковые ключи обратно в int
            user_balances = {int(k): v for k, v in data.get("user_balances", {}).items()}
            user_levels = {int(k): v for k, v in data.get("user_levels", {}).items()}
            user_total_earned = {int(k): v for k, v in data.get("user_total_earned", {}).items()}
            last_work_time = {int(k): v for k, v in data.get("last_work_time", {}).items()}
            
            logger.info(f"✅ Загружены данные пользователей: {len(user_balances)} пользователей")
        else:
            logger.info("📁 Файл данных не найден, создан новый")
            user_balances = {}
            user_levels = {}
            user_total_earned = {}
            last_work_time = {}
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки данных: {e}")
        # В случае ошибки создаем пустые словари
        user_balances = {}
        user_levels = {}
        user_total_earned = {}
        last_work_time = {}

# Глобальные переменные (загружаются из JSON файла)
user_balances = {}
user_levels = {}
user_total_earned = {}  # Общий заработок
last_work_time = {}
lepeshka_ready = False
ADMIN_ID = int(os.getenv("ADMIN_ID", 6134235469))
BOT_USERNAME = os.getenv("BOT_USERNAME", "@ashot3273_bot")

# Загружаем данные пользователей при запуске
load_user_data()

# Константы для музыки
MUSIC_SOURCES = {
    "hitmotop": {
        "url": "https://rus.hitmotop.com",
        "search_url": "https://rus.hitmotop.com/search?q={}",
        "song_url": "https://rus.hitmotop.com/song/{}",
        "download_url": "https://rus.hitmotop.com/download/{}"
    },
    "zaycev": {
        "url": "https://zaycev.net",
        "search_url": "https://zaycev.net/search.html?query_search={}",
        "song_url": "https://zaycev.net/song/{}",
        "download_url": "https://zaycev.net/mp3/{}"
    },
    "mp3party": {
        "url": "https://mp3party.net",
        "search_url": "https://mp3party.net/search?q={}",
        "song_url": "https://mp3party.net/music/{}",
        "download_url": "https://mp3party.net/download/{}"
    }
}

# Константы API
SNOOP_BOT_USERNAME = "@SnoopMusicbot"

# ==================== ФУНКЦИИ ДЛЯ YANDEX GPT ==================== #
def ask_yagpt(user_message: str, system_prompt: str) -> str:
    """Запрос к Yandex GPT"""
    if not IAM_TOKEN or not FOLDER_ID:
        logger.error("YandexGPT не настроен: отсутствует IAM_TOKEN или FOLDER_ID")
        return "Брат, я ща занят, давай попозже."

    headers = {
        "Authorization": f"Bearer {IAM_TOKEN}",
        "x-folder-id": FOLDER_ID,
        "Content-Type": "application/json"
    }
    
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/{MODEL_NAME}",
        "completionOptions": {
            "temperature": 0.6,
            "maxTokens": 1000,
            "stream": False
        },
        "messages": [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": user_message}
        ]
    }

    try:
        response = requests.post(YAGPT_API_URL, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        result = response.json()
        return result['result']['alternatives'][0]['message']['text']
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка запроса к YandexGPT: {e}")
        return "Брат, я ща занят, давай попозже."

def normalize_text(text):
    """Нормализация текста для обработки заказов"""
    text = text.lower()
    # Убираем только знаки препинания, оставляем русские буквы
    text = re.sub(r'[^\w\sа-яА-ЯёЁ]', '', text)
    
    words = text.split()
    normalized_words = []
    for word in words:
        for key, value in SYNONYMS.items():
            if word.startswith(key):
                normalized_words.append(value)
                break
        else:
            normalized_words.append(word)
    
    return " ".join(normalized_words)

# ==================== ФУНКЦИИ ДЛЯ МУЗЫКИ ==================== #
def start_image_generation(prompt: str) -> Optional[str]:
    """Запуск генерации изображения через Yandex Art"""
    if not IAM_TOKEN or not FOLDER_ID:
        return None

    headers = {
        "Authorization": f"Bearer {IAM_TOKEN}",
        "x-folder-id": FOLDER_ID,
        "Content-Type": "application/json"
    }
    
    data = {
        "modelUri": f"art://{FOLDER_ID}/yandex-art/latest",
        "messages": [{"text": prompt, "weight": 1}],
        "generationOptions": {"outputImageSpec": {"url": True}}
    }

    try:
        response = requests.post(
            YANDEX_ART_API_URL,
            headers=headers,
            json=data,
            timeout=150
        )
        response.raise_for_status()
        return response.json().get("id")
    except Exception as e:
        logger.error(f"Ошибка генерации изображения: {e}")
        return None

def check_operation(operation_id: str) -> Optional[str]:
    """Проверка статуса генерации изображения"""
    headers = {"Authorization": f"Bearer {IAM_TOKEN}"}
    try:
        response = requests.get(
            f"https://operation.api.cloud.yandex.net/operations/{operation_id}",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get("done", False):
            return result.get("response", {}).get("image", {}).get("url")
    except Exception as e:
        logger.error(f"Ошибка проверки операции: {e}")
    return None

async def search_vk(query: str) -> Optional[Tuple[str, str, str]]:
    """Поиск трека через VK API"""
    if not VK_ACCESS_TOKEN:
        logger.error("VK API не настроен: отсутствует VK_ACCESS_TOKEN")
        return None
        
    try:
        params = {
            "q": query,
            "access_token": VK_ACCESS_TOKEN,
            "v": "5.131",
            "count": 1,
            "auto_complete": 1,
            "sort": 2  # По популярности
        }
        
        response = requests.get(MUSIC_SOURCES["vk"]["search_url"], params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "response" in data and "items" in data["response"] and data["response"]["items"]:
            track = data["response"]["items"][0]
            title = track.get("title", "")
            artist = track.get("artist", "")
            url = track.get("url", "")
            
            if url:
                return title, artist, url
                
    except Exception as e:
        logger.error(f"Ошибка поиска в VK: {e}")
    return None

async def search_youtube(query: str) -> Optional[Tuple[str, str, str]]:
    """Поиск трека через YouTube API"""
    if not YOUTUBE_API_KEY:
        logger.error("YouTube API не настроен: отсутствует YOUTUBE_API_KEY")
        return None
        
    try:
        params = {
            "part": "snippet",
            "q": f"{query} audio",
            "type": "video",
            "maxResults": 1,
            "key": YOUTUBE_API_KEY
        }
        
        response = requests.get(MUSIC_SOURCES["youtube"]["search_url"], params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "items" in data and data["items"]:
            video = data["items"][0]
            video_id = video["id"]["videoId"]
            title = video["snippet"]["title"]
            channel = video["snippet"]["channelTitle"]
            
            # Формируем прямую ссылку на видео
            url = MUSIC_SOURCES["youtube"]["download_url"].format(video_id)
            return title, channel, url
                
    except Exception as e:
        logger.error(f"Ошибка поиска в YouTube: {e}")
    return None

async def search_song(query: str) -> Optional[Tuple[str, str, str]]:
    """Поиск трека на zaycev.net"""
    try:
        search_url = f"https://zaycev.net/search.html?query_search={requests.utils.quote(query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        resp = requests.get(search_url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        # Находим первую ссылку на песню
        song_link = soup.select_one("div.musicset-track__title a")
        if not song_link or not song_link.get("href"):
            return None
        song_url = "https://zaycev.net" + song_link.get("href")
        # Переходим на страницу песни
        song_resp = requests.get(song_url, headers=headers, timeout=15)
        song_resp.raise_for_status()
        song_soup = BeautifulSoup(song_resp.text, "html.parser")
        # Парсим название и исполнителя
        title = song_soup.select_one(".musicset-track__title").get_text(strip=True) if song_soup.select_one(".musicset-track__title") else query
        artist = song_soup.select_one(".musicset-track__artist").get_text(strip=True) if song_soup.select_one(".musicset-track__artist") else "Неизвестный исполнитель"
        # Парсим ссылку на mp3 (ищем data-url в кнопке)
        download_btn = song_soup.select_one(".musicset-track__download-btn")
        mp3_url = download_btn.get("data-url") if download_btn else None
        if not mp3_url:
            # Иногда mp3 ссылка бывает в script или другом месте, можно доработать при необходимости
            return None
        if not mp3_url.startswith("http"):
            mp3_url = "https://zaycev.net" + mp3_url
        return title, artist, mp3_url
    except Exception as e:
        logger.error(f"Ошибка поиска песни на zaycev.net: {e}")
        return None

async def download_mp3(mp3_url: str) -> Optional[Tuple[BytesIO, str]]:
    """Скачивание MP3 файла с zaycev.net"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://zaycev.net/"
        }
        resp = requests.get(mp3_url, headers=headers, timeout=30, stream=True)
        resp.raise_for_status()
        content_type = resp.headers.get('content-type', '')
        if 'audio' not in content_type and 'mp3' not in content_type and 'octet-stream' not in content_type:
            logger.error(f"Неверный тип контента: {content_type}")
            return None
        mp3_data = BytesIO()
        total_size = 0
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                mp3_data.write(chunk)
                total_size += len(chunk)
                if total_size > 50 * 1024 * 1024:
                    logger.error("Файл слишком большой")
                    return None
        mp3_data.seek(0)
        filename = mp3_url.split('/')[-1].split('?')[0]
        if not filename.endswith('.mp3'):
            filename += '.mp3'
        return mp3_data, filename
    except Exception as e:
        logger.error(f"Ошибка скачивания MP3: {e}")
        return None

# ==================== ОСНОВНЫЕ КОМАНДЫ БОТА ==================== #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.message.from_user
    chat_type = update.message.chat.type
    
    if chat_type == "private":
        await update.message.reply_text(
            f"Салам, {user.first_name}! Я Ашот, делаю шаурму.\n"
            "• /menu - показать меню\n"
            "• /balance - проверить баланс\n"
            "• /work - доступные работы\n"
            "• /help - помощь по командам\n"
        )
    else:
        await update.message.reply_text(
            f"Салам всем! Я Ашот, делаю шаурму.\n"
            "Чтобы начать, напишите мне в личку или используйте команды здесь:\n"
            "• /menu - показать меню\n"
            "• /balance - проверить баланс\n"
            "• /work - доступные работы\n"
            "• /help - помощь по командам\n"
        )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    chat_type = update.message.chat.type
    help_text = (
        "📜 Команды бота Ашота:\n\n"
        "🍔 Еда и напитки:\n"
        "• 'Мне шаурму в сырном и колу' - сделать заказ\n"
        "• /menu - показать меню\n"
        "💰 Финансы:\n"
        "• /balance - проверить баланс\n"
        "• /topup - пополнить баланс\n"
        "💼 Работа:\n"
        "• /work - доступные работы\n"
    )
    
    if chat_type == "private":
        help_text += (
        )
    
    await update.message.reply_text(help_text)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /menu"""
    menu_text = "🍔 Меню Ашота:\n\n"
    menu_text += "• Шаурма в сырном: 250 руб\n"
    menu_text += "• Две в сырном: 500 руб\n"
    menu_text += "• Шаурма обычная: 240 руб\n"
    menu_text += "• Две обычные: 480 руб\n"
    menu_text += "• Гигант XXL: 500 руб\n"
    menu_text += "• Люля: 240 руб\n"
    menu_text += "• Курица гриль: 390 руб\n"
    menu_text += "• Курица гриль в лаваше: 400 руб\n"
    menu_text += "• Чебурек: 80 руб\n"
    menu_text += "• Пирожок с картошкой: 50 руб\n"
    menu_text += "• Самса: 70 руб\n"
    menu_text += "• Лепешка: 45 руб\n\n"
    menu_text += "🥤 Напитки:\n"
    menu_text += "• Кола: 120 руб\n"
    menu_text += "• Махито (все виды): 100-110 руб\n"
    menu_text += "• Кофе 3 в 1: 50 руб\n"
    menu_text += "• Латте: 150 руб\n"
    menu_text += "• Капучино: 145 руб\n"
    menu_text += "• Чай: 45 руб\n\n"
    menu_text += f"💸 Пополнить баланс: /topup"
    await update.message.reply_text(menu_text)

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /balance"""
    user_id = update.message.from_user.id
    balance = user_balances.get(user_id, 0)
    level = user_levels.get(user_id, 0)
    total_earned = user_total_earned.get(user_id, 0)
    
    # Расчет прогресса до следующего уровня
    next_level = level + 1
    if next_level in LEVEL_REQUIREMENTS:
        next_level_req = LEVEL_REQUIREMENTS[next_level]
        progress = min(int(total_earned / next_level_req * 100), 100)
        progress_text = f"📈 До {next_level} уровня: {progress}% ({total_earned}/{next_level_req} руб)"
    else:
        progress_text = "🎉 Ты достиг максимального уровня!"
    
    await update.message.reply_text(
        f"💳 Твой баланс: {balance} рублей\n"
        f"🏆 Уровень: {level}\n"
        f"💰 Всего заработано: {total_earned} руб\n"
        f"{progress_text}\n\n"
        "Пополнить: /topup\n"
        "Работать: /work"
    )

async def work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать доступные работы и прогресс"""
    user_id = update.message.from_user.id
    
    # Инициализация данных пользователя
    if user_id not in user_balances:
        user_balances[user_id] = 0
    if user_id not in user_levels:
        user_levels[user_id] = 0
    if user_id not in user_total_earned:
        user_total_earned[user_id] = 0
    
    level = user_levels[user_id]
    total_earned = user_total_earned[user_id]
    
    # Расчет прогресса до следующего уровня
    next_level = level + 1
    if next_level in LEVEL_REQUIREMENTS:
        next_level_req = LEVEL_REQUIREMENTS[next_level]
        progress = min(int(total_earned / next_level_req * 100), 100)
    else:
        next_level_req = "MAX"
        progress = 100

    text = (
        f"💼 Твой уровень: {level}\n"
        f"💰 Всего заработано: {total_earned} руб.\n"
        f"📈 Прогресс до {next_level} уровня: {progress}%\n\n"
        "Доступные работы:\n"
    )
    
    for job, details in JOBS.items():
        if details["level"] <= level:
            status = "✅ Доступно"
        else:
            status = f"🔒 Требуется уровень {details['level']}"
        text += f"• {job}: {details['salary']} руб. {status}\n"
    
    text += "\nЧтобы заработать, используй команды:\n"
    text += "Мама дай в долг: 'мама дай в долг'\n"
    text += "Таксист: 'брат я выезжаю'\n"
    text += "Уборщица: 'я еду'\n"
    text += "Промоутер: 'возьмите пожалуйста листочек'\n"
    text += "Расклейщик: 'брат наклеил только половину'\n"
    text += "Официант: 'что закажите'\n"
    text += "Темщик: 'пойду на темку'\n"
    text += "Менеджер: 'брат, отчет готов'\n"
    
    await update.message.reply_text(text)

async def topup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /topup"""
    if update.message.reply_to_message:
        await update.message.reply_text("Для пополнения баланса админ должен ответить на это сообщение")
    else:
        await update.message.reply_text("Для пополнения баланса админ должен ответить на твоё сообщение командой")

async def add_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /add_money (только для админа)"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Ты не админ")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Ответь на сообщение пользователя, которому хочешь добавить деньги")
        return

    try:
        amount = int(context.args[0])
        if amount <= 0:
            raise ValueError
    except (IndexError, ValueError):
        await update.message.reply_text("Используй: /add_money [сумма]")
        return

    user_id = update.message.reply_to_message.from_user.id
    user_balances[user_id] = user_balances.get(user_id, 0) + amount
    save_user_data()  # Сохраняем данные после пополнения
    await update.message.reply_text(f"✅ Ваш баланс пополнен на {amount} руб. Текущий баланс: {user_balances[user_id]} руб")

async def lepeshka_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /lepeshka_status"""
    status = "✅ Готова! 45 руб" if lepeshka_ready else "🕒 Готовится (5 минут) 45 руб"
    await update.message.reply_text(f"Статус лепёшки: {status}")

async def lepeshka_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /lepeshka_toggle (только для админа)"""
    global lepeshka_ready
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Ты не админ")
        return
        
    lepeshka_ready = not lepeshka_ready
    status = "✅ готовы" if lepeshka_ready else "🕒 в процессе"
    await update.message.reply_text(f"Статус лепёшки изменён: {status}")

async def set_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /set_prompt (только для админа)"""
    global base_prompt
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Ты не админ")
        return

    if not context.args:
        await update.message.reply_text("Используй: /set_prompt [новый промт]")
        return

    new_prompt = ' '.join(context.args)
    base_prompt = new_prompt
    await update.message.reply_text("✅ Системный промт обновлен!")

async def set_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /set_level - установка уровня пользователю (только для админа)"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Ты не админ")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Ответь на сообщение пользователя, которому хочешь установить уровень")
        return

    try:
        level = int(context.args[0])
        if level < 0 or level > 10:
            await update.message.reply_text("Уровень должен быть от 0 до 10")
            return
    except (IndexError, ValueError):
        await update.message.reply_text("Используй: /set_level [уровень]")
        return

    user_id = update.message.reply_to_message.from_user.id
    old_level = user_levels.get(user_id, 0)
    user_levels[user_id] = level
    save_user_data()  # Сохраняем данные после изменения уровня
    await update.message.reply_text(f"✅ Уровень пользователя изменен на {level}")

# ==================== КОМАНДЫ: МУЗЫКА И ИЗОБРАЖЕНИЯ ==================== #
async def song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /song - поиск и отправка музыки с zaycev.net"""
    if not context.args:
        await update.message.reply_text("Брат, укажи название песни! Пример: /song Король и Шут")
        return
    query = " ".join(context.args)
    status_message = await update.message.reply_text(f"🔍 Ищу песню: {query}...")
    try:
        track_info = await search_song(query)
        if track_info:
            title, artist, mp3_url = track_info
            await status_message.edit_text(f"🎵 Нашел песню:\n📌 {title} - {artist}\n\n⏳ Скачиваю...")
            result = await download_mp3(mp3_url)
            if result:
                mp3_file, filename = result
                await status_message.edit_text(f"🎵 Нашел песню:\n📌 {title} - {artist}\n\n📤 Отправляю...")
                try:
                    await update.message.reply_audio(
                        audio=mp3_file,
                        title=title,
                        performer=artist,
                        filename=filename,
                        caption=f"🎧 Держи, брат: {title} - {artist}"
                    )
                    await status_message.delete()
                    return
                except Exception as e:
                    logger.error(f"Ошибка отправки файла: {e}")
                    await status_message.edit_text("😔 Не получилось отправить файл, брат")
                    return
        await status_message.edit_text("😔 Не получилось найти песню, брат")
    except Exception as e:
        logger.error(f"Ошибка при поиске песни: {e}")
        await status_message.edit_text("😔 Не получилось найти песню, брат")

async def draw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /draw - генерация изображений"""
    if not context.args:
        await update.message.reply_text("Брат, опиши что нарисовать! Пример: /draw шаурма в космосе")
        return
    
    prompt = " ".join(context.args)
    await update.message.reply_text(f"Генерирую: {prompt}...")
    
    # Запуск генерации
    operation_id = start_image_generation(prompt)
    if not operation_id:
        await update.message.reply_text("Не получилось запустить генерацию")
        return
    
    # Ожидание завершения (максимум 1 минута)
    image_url = None
    for _ in range(6):  # 6 попыток с интервалом 10 секунд
        await asyncio.sleep(10)
        image_url = check_operation(operation_id)
        if image_url:
            break
    
    if not image_url:
        await update.message.reply_text("Генерация заняла слишком долго")
        return
    
    # Скачивание и отправка изображения
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        image_data = BytesIO(response.content)
        await update.message.reply_photo(
            photo=image_data,
            caption=f"🖼 Держи, брат: {prompt}"
        )
    except Exception as e:
        logger.error(f"Ошибка отправки изображения: {e}")
        await update.message.reply_text("Не получилось отправить изображение")

async def all_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /all_balance - показать баланс всех пользователей (только для админа)"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Ты не админ")
        return

    if not user_balances:
        await update.message.reply_text("Пока нет пользователей с балансом")
        return

    # Сортируем пользователей по балансу (от большего к меньшему)
    sorted_users = sorted(user_balances.items(), key=lambda x: x[1], reverse=True)
    
    text = "💰 Баланс всех пользователей:\n\n"
    for user_id, balance in sorted_users:
        try:
            user = await context.bot.get_chat(user_id)
            username = user.username or user.first_name
            level = user_levels.get(user_id, 0)
            total_earned = user_total_earned.get(user_id, 0)
            text += f"👤 {username}:\n"
            text += f"   💳 Баланс: {balance} руб\n"
            text += f"   🏆 Уровень: {level}\n"
            text += f"   💰 Всего заработано: {total_earned} руб\n\n"
        except Exception as e:
            logger.error(f"Ошибка получения информации о пользователе {user_id}: {e}")
            continue

    await update.message.reply_text(text)

# ==================== ОБРАБОТКА ОБЫЧНЫХ СООБЩЕНИЙ ==================== #
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик обычных текстовых сообщений"""
    print(f"🔍 [DEBUG] Получено сообщение: {update.message.text}")
    print(f"🔍 [DEBUG] От пользователя: {update.message.from_user.id}")
    
    global lepeshka_ready
    text = update.message.text
    user_id = update.message.from_user.id
    current_time = time.time()
    chat_type = update.message.chat.type
    
    print(f"🔍 [DEBUG] Тип чата: {chat_type}")
    
    # Инициализация данных пользователя
    if user_id not in user_balances:
        user_balances[user_id] = 0
        print(f"🔍 [DEBUG] Инициализирован баланс для пользователя {user_id}")
    if user_id not in user_levels:
        user_levels[user_id] = 0
        print(f"🔍 [DEBUG] Инициализирован уровень для пользователя {user_id}")
    if user_id not in user_total_earned:
        user_total_earned[user_id] = 0
        print(f"🔍 [DEBUG] Инициализирован total_earned для пользователя {user_id}")
    if user_id not in last_work_time:
        last_work_time[user_id] = 0
        print(f"🔍 [DEBUG] Инициализирован last_work_time для пользователя {user_id}")
    
    normalized_text = normalize_text(text)
    logger.info(f"Normalized text: {normalized_text}")
    print(f"🔍 [DEBUG] Нормализованный текст: {normalized_text}")
    
    # Обработка рабочих команд
    for job, details in JOBS.items():
        commands = details["command"] if isinstance(details["command"], list) else [details["command"]]
        for command in commands:
            if command.lower() in normalized_text:
                logger.info(f"Matched job: {job} with command: {command}")
                
                if user_levels[user_id] < details["level"]:
                    await update.message.reply_text(f"Брат, для работы {job} нужен уровень {details['level']}!")
                    return
                
                # Проверка кулдауна (1 работа в час)
                if current_time - last_work_time[user_id] < 3600:
                    cooldown = int(3600 - (current_time - last_work_time[user_id]))
                    minutes = cooldown // 60
                    seconds = cooldown % 60
                    await update.message.reply_text(f"Отдохни, брат! Попробуй через {minutes} мин. {seconds} сек.")
                    return
                
                # Начисление зарплаты
                salary = details["salary"]
                old_balance = user_balances[user_id]
                user_balances[user_id] = old_balance + salary
                user_total_earned[user_id] += salary
                last_work_time[user_id] = current_time
                
                logger.info(f"Updated balance for user {user_id}: {old_balance} -> {user_balances[user_id]}")
                
                # Проверка повышения уровня
                old_level = user_levels[user_id]
                new_level = old_level
                
                # Проверяем все уровни на предмет достижения
                for level, requirement in sorted(LEVEL_REQUIREMENTS.items()):
                    if user_total_earned[user_id] >= requirement:
                        new_level = level
                
                level_up = new_level > old_level
                if level_up:
                    user_levels[user_id] = new_level
                
                save_user_data()  # Сохраняем данные после работы
                
                user_name = update.message.from_user.first_name
                response = f"💼 {user_name} ({job}): +{salary} руб.\nБаланс: {user_balances[user_id]} руб."
                if level_up:
                    response += f"\n🎉 Уровень UP! Теперь ты {user_levels[user_id]} lvl!"
                
                logger.info(f"Sending response: {response}")
                await update.message.reply_text(response)
                return
    
    # Обработка заказов и других сообщений
    if normalized_text.startswith("мне "):
        order_text = normalized_text[4:]
        items = [item.strip() for item in order_text.split(" и ") if item.strip()]
        
        total_price = 0
        order_details = []
        valid_order = True
        
        for item in items:
            # Обработка лепешки отдельно
            if item in ["лепешка", "лепешку"]:
                price = PRICES["лепешка"]
                total_price += price
                if lepeshka_ready:
                    order_details.append(f"Лепешка хорошо дорогой сделаю {price} руб")
                else:
                    order_details.append(f"Лепешка ща брат доделывается 5 минут {price} руб")
                continue
                
            drink_found = False
            for drink in ["колу", "махито клубничный", "махито оригинальный", "махито виноград", 
                         "кофе 3 в 1", "латте", "капучино", "чай зелёный", "чай чёрный"]:
                if drink in item:
                    price = PRICES[drink]
                    total_price += price
                    order_details.append(f"{DISPLAY_NAMES[drink]} брат сделаю {price} руб")
                    drink_found = True
                    break
            if drink_found:
                continue
                
            food_found = False
            for food in PRICES:
                if food in item:
                    quantity = 1
                    if item.startswith("2 ") or "две " in item:
                        quantity = 2
                        if food == "в сырном":
                            food = "две в сырном"
                        elif food == "в обычном":
                            food = "две в обычном"
                        elif food == "люля":
                            food = "две люля"
                    
                    price = PRICES[food]
                    total_price += price
                    
                    if food in ["махито клубничный", "махито оригинальный", "махито виноград", 
                               "кофе 3 в 1", "латте", "капучино", "чай зелёный", "чай чёрный"]:
                        response_text = f"{DISPLAY_NAMES[food]} брат сделаю {price} руб"
                    else:
                        response_text = f"{DISPLAY_NAMES[food]} хорошо дорогой сделаю {price} руб"
                    
                    order_details.append(response_text)
                    food_found = True
                    break
                    
            if not food_found:
                valid_order = False
                await update.message.reply_text(f"Брат, не понял: {item}")
                break
        
        if valid_order:
            if user_balances[user_id] < total_price:
                await update.message.reply_text("Брат, иди зарабатывать!")
            else:
                user_balances[user_id] -= total_price
                save_user_data()  # Сохраняем данные после покупки
                user_name = update.message.from_user.first_name
                response = f"Заказ для {user_name}:\n" + "\n".join(order_details)
                await update.message.reply_text(response)
    else:
        if "ашот" in normalized_text or "ашота" in normalized_text or BOT_USERNAME.lower() in normalized_text:
            user_message = update.message.text
            response_text = ask_yagpt(user_message, base_prompt)
            await update.message.reply_text(response_text)

if __name__ == '__main__':
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    if not TOKEN:
        raise ValueError("Не указан TELEGRAM_TOKEN в переменных окружения!")
    
    # Настройка обработки ошибок и переподключения
    max_retries = 5
    retry_delay = 10
    
    for attempt in range(max_retries):
        try:
            logger.info(f"🔄 Попытка запуска бота #{attempt + 1}")
            
            app = Application.builder().token(TOKEN).build()
            
            # Добавляем обработчики команд
            app.add_handler(CommandHandler("start", start))
            app.add_handler(CommandHandler("help", help))
            app.add_handler(CommandHandler("menu", menu))
            app.add_handler(CommandHandler("balance", balance))
            app.add_handler(CommandHandler("topup", topup))
            app.add_handler(CommandHandler("add_money", add_money))
            app.add_handler(CommandHandler("lepeshka_status", lepeshka_status))
            app.add_handler(CommandHandler("lepeshka_toggle", lepeshka_toggle))
            app.add_handler(CommandHandler("set_prompt", set_prompt))
            app.add_handler(CommandHandler("work", work))
            app.add_handler(CommandHandler("song", song))
            app.add_handler(CommandHandler("all_balance", all_balance))
            app.add_handler(CommandHandler("set_level", set_level))
            
            # Добавляем обработчик для всех типов чатов
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            
            logger.info("✅ Бот Ашот запущен и готов к работе!")
            
            # Запускаем бота с обработкой ошибок
            app.run_polling(
                drop_pending_updates=True,
                allowed_updates=None,
                timeout=30,
                bootstrap_retries=3,
                read_timeout=30,
                write_timeout=30,
                connect_timeout=30,
                pool_timeout=30
            )
            
            # Если мы дошли до этой точки, значит бот был остановлен корректно
            logger.info("🛑 Бот остановлен")
            break
            
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске бота (попытка {attempt + 1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"⏳ Ожидание {retry_delay} секунд перед повторной попыткой...")
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 300)  # Экспоненциальная задержка, максимум 5 минут
            else:
                logger.error("💥 Все попытки запуска исчерпаны!")
                raise