import asyncio
import random
from config import TG_API_ID, TG_API_HASH, TG_PHONE
from telethon import TelegramClient
from telethon.tl.types import PeerChannel
from openrouter_api import api

# Глобальный кеш для клиента Telegram
_tg_client = None

async def get_tg_client():
    """Асинхронный клиент Telegram с ленивой инициализацией"""
    global _tg_client
    if _tg_client is None:
        _tg_client = TelegramClient('rofls', TG_API_ID, TG_API_HASH)
        await _tg_client.start(phone=TG_PHONE)
    return _tg_client

async def async_get_post(name, index=1, is_rand=False):
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

async def gork(msg, event, bot):
    """Асинхронная обработка команды gork"""
    if not isinstance(msg, str):
        raise ValueError("msg must be string")
    
    reply = ""
    if event.reply_message:
        reply = f"\n\nКонтекст: \"{event.reply_message}\""
    
    content = await api.async_query(msg + reply)
    bot.send_message(content, event.peer_id)

async def axe(name, event, bot, index=1, is_rand=False):
    """Асинхронная обработка команды axe"""
    post = await async_get_post(name, index, is_rand)
    bot.send_message(post, event.peer_id)

async def tag(event, bot):
    """Асинхронная обработка входящих команд"""
    if not event.message:
        return
    
    try:
        msg = event.message.strip()
        if not msg:
            return
        
        parts = msg.split(maxsplit=1)
        tag = parts[0].lstrip("@").rstrip(",").lower()
        rest_msg = parts[1] if len(parts) > 1 else ""
        
        # Обработка команды gork
        if tag == "gork" or tag == "горк":
            await gork(rest_msg, event, bot)
            return
        
        # Определение параметров для команд
        is_rand = rest_msg.lower() == "рандом"
        index = 1
        if rest_msg.isdigit():
            index = int(rest_msg)
        
        # Обработка команд каналов
        if tag == "топор":
            await axe(PeerChannel(1237513492), event, bot, index, is_rand)
        elif tag == "ньюсач":
            await axe("ru2ch", event, bot, index, is_rand)
        elif tag == "униан":
            await axe("uniannet", event, bot, index, is_rand)
        elif tag == "поздняков":
            await axe(PeerChannel(1732054517), event, bot, index, is_rand)
            
    except Exception as e:
        print(f"Ошибка обработки команды: {e}")
        bot.send_message("⚠️ Произошла ошибка при обработке команды", event.peer_id)
