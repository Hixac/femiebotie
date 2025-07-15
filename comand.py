import db
import asyncio
import random
import error_handle as eh
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
    await bot.send_message(content, event.peer_id)

async def axe(name, event, bot, index=1, is_rand=False):
    """Асинхронная обработка команды axe"""
    post = await async_get_post(name, index, is_rand)
    await bot.send_message(post, event.peer_id)

def fancy_top(num, sec_name, name, msg_count):
    template = f"{name} {sec_name} написал {msg_count} сообщений"
    fire = "🔥"; snowman = "⛄"; flower = "🌼"; nl = "\n"
    if num == 1:
        return fire * 3 + template + fire * 3 + nl
    if num == 2:
        return snowman * 2 + template + snowman * 2 + nl
    if num == 3:
        return flower + template + flower + nl
    if num == 4:
        return "\n\n😽ОСТАЛЬНЫМ СПАСИБКИ ЗА АКТИВ😽\n\n" + f"{str(num)}. " + template + nl

    return f"{str(num)}. " + template + nl
    
async def get_top_members(bot, peer_id):
    mems = db.get_top_members(peer_id)
    ans = "🐒🦄 НАШИ ТОПОВЫЕ АКТИВЧИКИ ⭐\n\n"
    for i in range(10):
        vk_id = mems[i][1]; msg_count = mems[i][5]
        person = db.get_user(vk_id)
        ans += fancy_top(i + 1, person[1], person[2], msg_count)

    await bot.send_message(ans, peer_id)

async def get_admins(bot, peer_id):
    mems = db.get_admin_members(peer_id)
    ans = "Список админов\n\n"
    for i in range(len(mems)):
        vk_id = mems[i][1]
        person = db.get_user(vk_id)
        ans += f"{i + 1}. {person[2]} {person[1]}\n"
    
    await bot.send_message(ans, peer_id)

async def get_owner(bot, peer_id):
    mems = db.get_owner(peer_id)
    if len(mems) == 0:
        await bot.send_message("Основателем является паблик", peer_id)
        return
        
    ans = "Основатель: "
    vk_id = mems[0][1]
    person = db.get_user(vk_id)
    ans += f"{person[2]} {person[1]}"
    
    await bot.send_message(ans, peer_id)

def is_owner(event):
    owner = db.get_owner(event.peer_id) 
    return len(owner) > 0 and owner[0][1] == event.author_id

def is_admin(event):
    admins = db.get_admin_members(event.peer_id)
    admins = [i[1] for i in admins]
    return len(admins) > 0 and event.author_id in admins

@eh.handle_exception(default_response=eh.automatic_response, conn_error=eh.connection_response)
async def tag(event, bot):
    """Асинхронная обработка входящих команд"""
    if not event.message:
        return

    msg = event.message.strip()
    if not msg:
        return
    
    parts = msg.split(maxsplit=1)
    tag = parts[0].lstrip("@").rstrip(",").lower()
    rest_msg = parts[1] if len(parts) > 1 else ""

    if tag == 'sql' and is_owner(event):
        await bot.send_message(str(db.query(rest_msg)), event.peer_id)
        return
        
    # Обработка команды gork
    if tag == "gork" or tag == "горк":
        await gork(rest_msg, event, bot)
        return

    if tag == "основатель":
        await get_owner(bot, event.peer_id)
        return
        
    if tag == "админы":
        await get_admins(bot, event.peer_id)
        return
        
    if tag == "активы":
        await get_top_members(bot, event.peer_id)
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
