from config import TG_API_ID, TG_API_HASH, TG_PHONE
from telethon import TelegramClient
from telethon.tl.types import PeerChannel

import random

convert_id = PeerChannel

_tg_client = None

async def get_tg_client():
    """Асинхронный клиент Telegram с ленивой инициализацией"""
    global _tg_client
    if _tg_client is None:
        _tg_client = TelegramClient('rofls', TG_API_ID, TG_API_HASH)
        await _tg_client.start(phone=TG_PHONE)
    return _tg_client

async def get_post(name, index=1, is_rand=False):
    """Асинхронное получение поста из Telegram канала"""
    if not isinstance(is_rand, bool):
        raise ValueError("is_rand must be boolean")
    if not isinstance(index, int):
        raise ValueError("index must be integer")
    
    client = await get_tg_client()
    channel = await client.get_entity(name)
    
    if is_rand:
        messages = []
        async for msg in client.iter_messages(channel, limit=100):
            if msg.text:
                messages.append(msg.text)
        return random.choice(messages) if messages else "Не найдено сообщений"
    
    messages = []
    async for msg in client.iter_messages(channel, limit=index):
        if msg.text:
            messages.append(msg.text)

    return messages[-1] if messages else "Не найдено сообщений"
