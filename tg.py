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

async def get_post(chat, index=0, is_rand=False):
    if not isinstance(is_rand, bool):
        raise ValueError("is_rand must be boolean")
    if not isinstance(index, int):
        raise ValueError("index must be integer")
    
    client = await get_tg_client()
    channel = await client.get_entity(chat)
    
    if is_rand:
        index = random.randint(0, 1000)

    counter = index
    async for msg in client.iter_messages(chat, limit=index+1):
        message = msg
        if counter == 0:
            break
        counter -= 1
    
    media = []
    if message.media is not None and message.photo:
        if message.grouped_id is not None:
            search_ids = [i for i in range(message.id - 10, message.id + 10 + 1)]
            posts = await client.get_messages(chat, ids=search_ids)
            media = []
            for post in posts:
                if post is not None and post.grouped_id == message.grouped_id and post.photo is not None:
                    media.append(await post.download_media())
        else:
            media.append(await client.download_media(message.media))

    return (message.text, media)
