import db
import asyncio
import random
import error_handle as eh
from config import TG_API_ID, TG_API_HASH, TG_PHONE
from telethon import TelegramClient
from telethon.tl.types import PeerChannel
from openrouter_api import api
import aiohttp
import aiofiles
import validators
from bs4 import BeautifulSoup

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
        reply = f"\n\nКонтекст: \"{event.reply_message[1]}\""
    
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
    for i in range(min(len(mems), 10)):
        vk_id = mems[i].vk_id; msg_count = mems[i].msg_count
        person = db.get_user(vk_id)
        ans += fancy_top(i + 1, person.sec_name, person.name, msg_count)

    await bot.send_message(ans, peer_id)

async def get_admins(bot, peer_id):
    mems = db.get_admin_members(peer_id)
    ans = "Список админов\n\n"
    for i in range(len(mems)):
        vk_id = mems[i].vk_id
        person = db.get_user(vk_id)
        ans += f"{i + 1}. {person.name} {person.sec_name}\n"
    
    await bot.send_message(ans, peer_id)

async def get_owner(bot, peer_id):
    owner = db.get_owner(peer_id)
    if owner is None:
        await bot.send_message("Основателем является паблик", peer_id)
        return
        
    ans = "Основатель: "
    vk_id = owner.vk_id
    person = db.get_user(vk_id)
    ans += f"{person.name} {person.sec_name}"
    
    await bot.send_message(ans, peer_id)

def is_owner(event):
    owner = db.get_owner(event.peer_id) 
    return not (owner is None) and owner.vk_id == event.author_id

def is_admin(event):
    admins = db.get_admin_members(event.peer_id)
    admins = [i[1] for i in admins]
    return len(admins) > 0 and event.author_id in admins

async def who_am_i(vk_id, peer_id, bot):    
    base_info = db.get_user(vk_id)
    user_chat_info = db.get_user_chat(vk_id, peer_id)

    ans = "СТАТЫ\n"
    ans += "👀Информация об " + base_info.sec_name + " " + base_info.name
    ans += "\n\nНаписал сообщений " + str(user_chat_info.msg_count)
    if user_chat_info.is_owner:
        ans += "\nЯвляется основателем!!!✍"
    else: ans += "\nНе является основателем...😪"
    if user_chat_info.is_admin:
        ans += "\nЯвляется админчиком!!!🤩"
    else: ans += "\nНе является админом...😰"
    
    await bot.send_message(ans, peer_id)

async def who_are_you(event, bot):
    reply = event.reply_message
    if len(reply) == 0:
        return #add behaviour
    await who_am_i(reply[0], event.peer_id, bot)

async def download_img(url, yt_id):
    import os
    filename = os.getcwd() + "/" + yt_id + '.png'
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(filename, mode='wb')
                await f.write(await resp.read())
                await f.close()

    return filename

# https://www.youtube.com/shorts/x3lWKm9cE5E
# https://www.youtube.com/watch?v=db67SLeT8IE&t=52s
def get_yt_id(url):
    start = url.find("shorts")
    if start != -1:
        start += len("shorts") + 1
    else:
        start = url.find("=") + 1        
    return url[start:start+11]

async def parse_yt_url(event, bot):
    async with aiohttp.ClientSession() as session:
        async with session.get(event.message) as r:
            soup = BeautifulSoup(await r.text(), "html.parser")
            link = soup.find_all(name="title")[0]
            title = str(link)
            title = title.replace("<title>","")
            title = title.replace("</title>","")

            img = await download_img("https://img.youtube.com/vi/" + get_yt_id(event.message) + "/hqdefault.jpg", get_yt_id(event.message))
            await bot.send_message(title[:-9], event.peer_id, photo_dir=img)
    
@eh.handle_exception(default_response=eh.automatic_response, conn_error=eh.connection_response)
async def tag(event, bot):
    """Асинхронная обработка входящих команд"""
    if not event.message:
        return

    msg = event.message.strip().lower()
    if not msg:
        return
    
    parts = msg.split(maxsplit=1)
    tag = parts[0].lstrip("@").rstrip(",").lower()
    rest_msg = parts[1] if len(parts) > 1 else ""

    if (msg.find("youtube.com") != -1 or msg.find("youtu.be")) and validators.url(event.message):
        await parse_yt_url(event, bot)
        return
    
    if msg == "кто ты":
        await who_are_you(event, bot)
        return
    
    if msg == "кто я":
        await who_am_i(event.author_id, event.peer_id, bot)
        return
    
    if tag == 'sql' and is_owner(event):
        await bot.send_message(str(db.query(rest_msg)), event.peer_id)
        return
        
    # Обработка команды gork
    if tag == "gork" or tag == "горк":
        await gork(rest_msg, event, bot)
        return

    if msg == "/основатель":
        await get_owner(bot, event.peer_id)
        return
        
    if msg == "/админы":
        await get_admins(bot, event.peer_id)
        return
        
    if msg == "/активы":
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
