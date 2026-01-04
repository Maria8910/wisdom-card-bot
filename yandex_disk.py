import os
import random
import requests
from typing import Optional, List


class YandexDiskClient:
    """Клиент для работы с Яндекс Диском"""
    
    def __init__(self, token: str, folder_path: str = '/Wisdom_Cards'):
        """
        Инициализация клиента
        
        Args:
            token: OAuth токен Яндекс Диска
            folder_path: Путь к папке с картинками на Яндекс Диске
        """
        self.token = token
        self.folder_path = folder_path
        self.base_url = 'https://cloud-api.yandex.net/v1/disk'
        self.headers = {
            'Authorization': f'OAuth {token}'
        }
        self._cached_files = None
    
    def _get_files_list(self) -> List[dict]:
        """
        Получает список всех файлов в папке
        
        Returns:
            Список файлов с метаданными
        """
        if self._cached_files is not None:
            return self._cached_files
        
        url = f'{self.base_url}/resources'
        params = {
            'path': self.folder_path,
            'limit': 1000  # Максимальное количество файлов
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            # Фильтруем только файлы (не папки) и изображения
            files = [
                item for item in data.get('_embedded', {}).get('items', [])
                if item.get('type') == 'file' and self._is_image(item.get('name', ''))
            ]
            
            self._cached_files = files
            return files
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении списка файлов: {e}")
            return []
    
    def _is_image(self, filename: str) -> bool:
        """Проверяет, является ли файл изображением"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        return any(filename.lower().endswith(ext) for ext in image_extensions)
    
    def _get_public_url(self, file_path: str) -> Optional[str]:
        """
        Получает публичную ссылку на файл
        
        Args:
            file_path: Путь к файлу на Яндекс Диске
            
        Returns:
            Публичная ссылка или None
        """
        url = f'{self.base_url}/resources/download'
        params = {'path': file_path}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get('href')
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении публичной ссылки: {e}")
            return None
    
    def get_random_image(self) -> Optional[str]:
        """
        Получает случайную картинку из папки
        
        Returns:
            URL случайной картинки или None
        """
        files = self._get_files_list()
        
        if not files:
            print("Не найдено изображений в папке")
            return None
        
        # Выбираем случайный файл
        random_file = random.choice(files)
        file_path = random_file.get('path')
        
        # Получаем публичную ссылку
        public_url = self._get_public_url(file_path)
        
        return public_url
    
    def clear_cache(self):
        """Очищает кэш списка файлов"""
        self._cached_files = None


