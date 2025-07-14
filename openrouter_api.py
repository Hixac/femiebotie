import os
import requests
import aiohttp
import asyncio
import config

class OpenrouterAPI:
    def __init__(self):
        self._api_key = config.OPEN_ROUTER_API_KEY_1
        self._url = "https://openrouter.ai/api/v1/chat/completions"
        self._session = None  # Для асинхронной сессии

    def query(self, prompt):
        """Синхронная версия запроса"""
        headers = {
            'Authorization': f'Bearer {self._api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': 'qwen/qwen3-235b-a22b:free',
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
        }

        try:
            response = requests.post(self._url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            return f"Ошибка запроса: {e}"
        except KeyError:
            return "Ошибка формата ответа API"

    async def async_query(self, prompt):
        """Асинхронная версия запроса"""
        headers = {
            'Authorization': f'Bearer {self._api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
        }

        # Ленивая инициализация сессии
        if self._session is None:
            self._session = aiohttp.ClientSession()

        try:
            async with self._session.post(self._url, headers=headers, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                return data['choices'][0]['message']['content']
        except aiohttp.ClientError as e:
            return f"Ошибка сетевого запроса: {e}"
        except KeyError:
            return "Ошибка формата ответа API"
        except Exception as e:
            return f"Неизвестная ошибка: {e}"

    async def close(self):
        """Закрытие асинхронной сессии при завершении"""
        if self._session:
            await self._session.close()
            self._session = None

# Глобальный экземпляр API
api = OpenrouterAPI()

# Функция для корректного закрытия при завершении приложения
async def cleanup():
    await api.close()
