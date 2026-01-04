"""
Скрипт для проверки подключения к API Яндекс Диска и Telegram
"""
import os
import sys
from dotenv import load_dotenv
import requests
import config

# Загружаем переменные окружения (если есть .env файл)
load_dotenv()

def test_yandex_disk():
    """Проверка подключения к Яндекс Диску"""
    token = os.getenv('YANDEX_DISK_TOKEN') or config.YANDEX_DISK_TOKEN
    folder_path = os.getenv('YANDEX_DISK_FOLDER') or config.YANDEX_DISK_FOLDER
    
    if not token:
        print("❌ YANDEX_DISK_TOKEN не найден в .env файле")
        return False
    
    print(f"📁 Проверка доступа к папке: {folder_path}")
    
    url = 'https://cloud-api.yandex.net/v1/disk/resources'
    headers = {'Authorization': f'OAuth {token}'}
    params = {'path': folder_path, 'limit': 1000}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        items = data.get('_embedded', {}).get('items', [])
        images = [item for item in items if item.get('type') == 'file' and 
                 any(item.get('name', '').lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'])]
        
        print(f"✅ Подключение к Яндекс Диску успешно!")
        print(f"📊 Найдено файлов в папке: {len(items)}")
        print(f"🖼️  Найдено изображений: {len(images)}")
        
        if images:
            print("\nПримеры найденных изображений:")
            for img in images[:5]:  # Показываем первые 5
                print(f"  - {img.get('name')}")
        
        return True
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            print(f"❌ Папка {folder_path} не найдена на Яндекс Диске")
        elif response.status_code == 401:
            print("❌ Неверный токен Яндекс Диска")
        else:
            print(f"❌ Ошибка при подключении к Яндекс Диску: {e}")
            print(f"   Код ответа: {response.status_code}")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def test_telegram_bot():
    """Проверка токена Telegram бота"""
    token = os.getenv('TELEGRAM_BOT_TOKEN') or config.TELEGRAM_BOT_TOKEN
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN не найден в config.py или .env файле")
        return False
    
    print(f"\n🤖 Проверка токена Telegram бота...")
    
    url = f'https://api.telegram.org/bot{token}/getMe'
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        if data.get('ok'):
            bot_info = data.get('result', {})
            print(f"✅ Токен Telegram бота валиден!")
            print(f"   Имя бота: @{bot_info.get('username')}")
            print(f"   Название: {bot_info.get('first_name')}")
            return True
        else:
            print(f"❌ Ошибка API Telegram: {data.get('description')}")
            return False
            
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            print("❌ Неверный токен Telegram бота")
        else:
            print(f"❌ Ошибка при подключении к Telegram API: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


if __name__ == '__main__':
    print("=" * 50)
    print("Проверка конфигурации бота")
    print("=" * 50)
    
    yandex_ok = test_yandex_disk()
    telegram_ok = test_telegram_bot()
    
    print("\n" + "=" * 50)
    if yandex_ok and telegram_ok:
        print("✅ Все проверки пройдены! Бот готов к запуску.")
        sys.exit(0)
    else:
        print("❌ Обнаружены проблемы. Проверьте конфигурацию.")
        sys.exit(1)

