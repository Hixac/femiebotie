from random import randint
from config import TG_API_ID, TG_API_HASH, TG_PHONE
from telethon.sync import TelegramClient
from telethon.tl.types import PeerChannel
from openrouter_api import api
from main import Bot

client = TelegramClient('rofls', TG_API_ID, TG_API_HASH)

def get_post(name, index = 1, is_rand = False):
    if not isinstance(is_rand, bool):
        raise ValueError("Restricted type")
    if not isinstance(index, int):
        raise ValueError("Restricted type")
    client.start(phone=TG_PHONE)
    channel = client.get_entity(name)

    l = []
    if is_rand:
        for msg in client.iter_messages(channel, limit=100):
            l.append(msg.text)
        return l[randint(0, 99)]
    
    for msg in client.iter_messages(channel, limit=index):
        l.append(msg.text)
        
    return l[-1]

def gork(msg, bot):
    if not isinstance(msg, str):
        raise ValueError("Restricted type")
    reply = ""
    if bot.last_event.reply_message != "":
        reply = "\n\nКонтекст: \"" + bot.last_event.reply_message + "\""
    content = api.query(msg + reply)
    bot.send_message(content, bot.last_event.peer_id)

def axe(name, bot, index = 1, is_rand = False):
    bot.send_message(get_post(name, index, is_rand), bot.last_event.peer_id)    
    
def tag(msg, bot):
    if not isinstance(msg, str):
        raise ValueError("Restricted type")
    if len(msg) == 0:
        return

    try:    
        rest_msg = msg.split()
        tag = rest_msg[0].lstrip("@").rstrip(",")
        rest_msg = " ".join(msg.split()[1:])
        
        if tag.lower() == "gork":
            gork(rest_msg, bot)

        is_rand = False
        if rest_msg == "рандом":
            is_rand = True

        index = 1
        if rest_msg.isnumeric():
            index = int(rest_msg)
            
        if tag.lower() == "топор":
            axe(PeerChannel(1237513492), bot, index, is_rand)
                
        if tag.lower() == "ньюсач":
            axe("ru2ch", bot, index, is_rand)
        
        if tag.lower() == "униан":
            axe("uniannet", bot, index, is_rand)
    except Exception as e:
        print(e)
