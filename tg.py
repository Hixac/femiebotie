from config import TG_API_ID, TG_API_HASH, TG_PHONE
from telethon import TelegramClient
from telethon.tl.types import PeerChannel

import random

convert_id = PeerChannel

_tg_client = None

async def get_tg_client():
    global _tg_client
    if _tg_client is None:
        _tg_client = TelegramClient('rofls', TG_API_ID, TG_API_HASH)
        await _tg_client.start(phone=TG_PHONE)
    return _tg_client

async def get_post(name, index=0, is_rand=False):
    if not isinstance(is_rand, bool):
        raise ValueError("is_rand must be boolean")
    if not isinstance(index, int):
        raise ValueError("index must be integer")
    
    client = await get_tg_client()
    channel = await client.get_entity(name)
    
    messages = []
    async for msg in client.iter_messages(channel, limit=(index+1 if not is_rand else 100)):
        if msg.text:
            messages.append(msg)

    message = messages[-1]
    if is_rand:
        message = random.choice(messages)

    media = ""
    if message.media is not None and message.photo:
        media = await client.download_media(message.media)

    return (message.text, media)
