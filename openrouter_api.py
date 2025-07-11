import os
import requests
import config

class OpenrouterAPI:
    def __init__(self):
        self._api_key = config.OPEN_ROUTER_API_KEY_1
        self._url = "https://openrouter.ai/api/v1/chat/completions"

    def query(self, prompt):
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
            return f"{e}"
        
api = OpenrouterAPI()
