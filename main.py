from bot_interface import Bot, Keyboard, ButtonColor, CallbackType
from async_stuff import throttle
import error_handle as eh
import openrouter_api
import db, tg

bot = Bot()

@bot.tag("/do")
@eh.handle_exception(default_response=eh.automatic_response, conn_error=eh.connection_response)
def action(event):
    user = db.get_user(event.author_id)
    ans = event.message[len('/do') + 1:]
    bot.send_message(f"{user.name} {user.sec_name} {ans}", event.peer_id)

@bot.comand("/гембл", "гемблинг")
@eh.handle_exception(default_response=eh.automatic_response, conn_error=eh.connection_response)
def hint_gambling(event):
    bot.send_message("Использование: /гембл [ставка]\nЧем выше ставка, тем больше мультипликатор. Игрой является очко.", event.peer_id)

@bot.tag("/гембл", "гемблинг", take_args=1) # TODO: fix the issues with buttons
@eh.handle_exception(default_response=eh.automatic_response, conn_error=eh.connection_response)
def gambling(event):
    class Card:
        def __init__(self, suit, value, extra=""):
            self.s = suit
            self.v = value
            self.extra = extra

        def __str__(self):
            if self.extra:
                return f"{self.s}{self.extra}"
            
            return f"{self.s}{self.v}"

    my_cards = []
    opponent_cards = []
    
    deck = [Card("♠️", 1, "туз"), Card("♠️", 2), Card("♠️", 3), Card("♠️", 4), Card("♠️", 5), Card("♠️", 6), Card("♠️", 7), \
            Card("♠️", 8), Card("♠️", 9), Card("♠️", 10), Card("♠️", 2, "валет"), Card("♠️", 3, "дама"), Card("♠️", 4, "король"), \
            Card("♥️", 1, "туз"), Card("♥️", 2), Card("♥️", 3), Card("♥️", 4), Card("♥️", 5), Card("♥️", 6), Card("♥️", 7), \
            Card("♥️", 8), Card("♥️", 9), Card("♥️", 10), Card("♥️", 2, "валет"), Card("♥️", 3, "дама"), Card("♥️", 4, "король"), \
            Card("♦️", 1, "туз"), Card("♦️", 2), Card("♦️", 3), Card("♦️", 4), Card("♦️", 5), Card("♦️", 6), Card("♦️", 7), \
            Card("♦️", 8), Card("♦️", 9), Card("♦️", 10), Card("♦️", 2, "валет"), Card("♦️", 3, "дама"), Card("♦️", 4, "король"), \
            Card("♣️", 1, "туз"), Card("♣️", 2), Card("♣️", 3), Card("♣️", 4), Card("♣️", 5), Card("♣️", 6), Card("♣️", 7), \
            Card("♣️", 8), Card("♣️", 9), Card("♣️", 10), Card("♣️", 2, "валет"), Card("♣️", 3, "дама"), Card("♣️", 4, "король")]
    from random import shuffle
    shuffle(deck)

    def show_my_cards():
        return ' '.join([str(i) for i in my_cards[:min(len(my_cards), 5)]])

    def show_opponent_cards():
        return ' '.join([str(i) for i in opponent_cards[:min(len(opponent_cards), 5)]])

    def my_sum():
        return sum(i.v for i in my_cards[:min(len(my_cards), 5)])

    def opponent_sum():
        return sum(i.v for i in opponent_cards[:min(len(opponent_cards), 5)])

    def end_stage():
        nonlocal bet, playing_with
        ans = ""
        if opponent_sum() > 21:
            ans += "\n\nТы проиграл, вся ставка моя."
            db.sub_coins(playing_with, event.peer_id, bet)
        elif opponent_sum() <= 21 and my_sum() == 21:
            ans += "\n\nПолная неудача, вся ставка моя."
            db.sub_coins(playing_with, event.peer_id, bet)
        elif opponent_sum() <= 21 and my_sum() > 21:
            ans += "\n\nТы победил, признаю, держи мои бабки."
            db.add_coins(playing_with, event.peer_id, bet)
        elif opponent_sum() > my_sum():
            ans += "\n\nГоспожа Удача улыбается тебе, жри свои ебаные сатошки."
            db.add_coins(playing_with, event.peer_id, bet)
        elif opponent_sum() <= my_sum():
            ans += "\n\nСоси, лмао. Я победитель по жизни."
            db.sub_coins(playing_with, event.peer_id, bet)
        return ans
            
    @bot.by_callback_type(CallbackType.GAMBLING_GAME_GRAB)
    @eh.handle_exception(default_response=eh.automatic_response, conn_error=eh.connection_response)
    def grab(event):
        nonlocal playing_with, bet
        if event.author_id != playing_with:
            return
        opponent_cards.append(deck.pop())
        my_cards.append(deck.pop())
        ans = f"Твоя карта {str(opponent_cards[-1])}"
        if len(opponent_cards) > 1:
            ans = f"Твои карты {show_opponent_cards()}"
            ans += f"\nВ сумме будет {str(opponent_sum())}"

        kbd = Keyboard(inline=True)
        if len(opponent_cards) < 5:
            kbd.add_callback_button("Вытянуть карту", ButtonColor.PRIMARY, payload={"callback_type": CallbackType.GAMBLING_GAME_GRAB})
            kbd.add_line()
        kbd.add_callback_button("Показать карты", ButtonColor.PRIMARY, payload={"callback_type": CallbackType.GAMBLING_GAME_SHOW})
        bot.edit_message(ans, event.callback_conv_msg_id, event.peer_id, keyboard=kbd.get_keyboard())

    @bot.by_callback_type(CallbackType.GAMBLING_GAME_SHOW)
    @eh.handle_exception(default_response=eh.automatic_response, conn_error=eh.connection_response)
    def show(event):
        nonlocal playing_with, bet
        if event.author_id != playing_with:
            return
        ans = f"Твои карты {show_opponent_cards()}"
        ans += f"\nВ сумме будет {str(opponent_sum())}"
        ans += f"\nРаскрываемся. Мои карты: {show_my_cards()}"
        ans += f", что в сумме {str(my_sum())}."
        ans += end_stage()
                
        bot.edit_message(ans, event.callback_conv_msg_id, event.peer_id)
        return
    
    bet = event.message.split()[-1]
    if not bet.isnumeric() or int(bet) > db.get_coins(event.author_id, event.peer_id):
        bot.send_message("Ставку нужно писать в числах, в пределах твоих сатош.", event.peer_id)
        return

    bet = int(bet)
    playing_with = event.author_id
    user = db.get_user(playing_with)
    
    kbd = Keyboard(inline=True)
    kbd.add_callback_button("Вытянуть карту", ButtonColor.PRIMARY, payload={"callback_type": CallbackType.GAMBLING_GAME_GRAB})
    bot.send_message(f"Игра в Очко с {user.name} {user.sec_name} началась.\n\nЯ вытянул первую карту.", event.peer_id, keyboard=kbd.get_keyboard())

@bot.tag("слотмашина", "слот машина") # TODO: add button
@eh.handle_exception(default_response=eh.automatic_response, conn_error=eh.connection_response)
def slot_machine(event):

    if db.get_coins(event.author_id, event.peer_id) < 10:
        bot.send_message("Ебать ты нищуган, съеби с казино, тебе тут не рады.", event.peer_id)
        return
    db.sub_coins(event.author_id, event.peer_id, 10)
    
    from random import choice
    
    emojis = ["✅", "🦈", "⛳", "🤹", "♀", "🇷🇺"]

    e1 = choice(emojis)
    e2 = choice(emojis)
    e3 = choice(emojis)
    
    ans = f"""+-----+-----+-----+
| {e1} | {e2} | {e3} |
+-----+-----+-----+"""

    bot.send_message(ans, event.peer_id)
    
    if e1 + e2 + e3 == "🇷🇺🇷🇺🇷🇺":
        db.add_coins(event.author_id, event.peer_id, 2000)
        bot.send_message("ВЫ ВЫИГРАЛИ СУПЕРГОЙДА ПРИЗ!! ВЫИГРЫШ СОСТАВЛЯЕТ 2000 САТОШ.", event.peer_id)
    elif e1 == e2 and e2 == e3:
        db.add_coins(event.author_id, event.peer_id, 500)
        bot.send_message("Победа! Вам присуждается 500 сатош.", event.peer_id)

@bot.header("СМЕНА ИМЕНИ")
@eh.handle_exception(default_response=eh.automatic_response, conn_error=eh.connection_response)
def changer(event):
    coins = db.get_coins(event.author_id, event.peer_id)
    if coins < 1000:
        bot.send_message(f"Съеби, ебана. (У вас {coins} сатоши)", event.peer_id)
        return
    
    if len(event.message) >= 50:
        bot.send_message("Слишком длинное имя, надо ужаться в 50 символов, еблан.", event.peer_id)
        return

    db.sub_coins(event.author_id, event.peer_id, 1000)
    db.change_sec_name(event.author_id, event.message)
    bot.send_message("Сменил имя на ДЫРЯВЫЙ... Шучу. Изменил имя.", event.peer_id)

@bot.header("СМЕНА ФАМИЛИИ")
@eh.handle_exception(default_response=eh.automatic_response, conn_error=eh.connection_response)
def changer(event):
    coins = db.get_coins(event.author_id, event.peer_id)
    if coins < 1000:
        bot.send_message(f"Не машни передо мной без бабла. (У вас {coins} сатоши)", event.peer_id)
        return
    
    if len(event.message) >= 50:
        bot.send_message("Слишком длинная фамилия, надо ужаться в 50 символов, еблан.", event.peer_id)
        return
    
    db.sub_coins(event.author_id, event.peer_id, 1000)
    db.change_name(event.author_id, event.message)
    bot.send_message("Сменил фамилию на ДОЛБАЕБ... Шучу. Изменил фамилию.", event.peer_id)
    
@bot.by_callback_type(CallbackType.MARKET)
@eh.handle_exception(default_response=eh.automatic_response, conn_error=eh.connection_response)
def stats_check(event):
    chose = event.callback_payload["chose"]

    if db.get_coins(event.author_id, event.peer_id) < 1000:
        bot.edit_message("Нищее ты хуйло, отъебись от меня.", event.callback_conv_msg_id, event.peer_id)
        return
    
    if chose == 1:
        bot.edit_message("СМЕНА ИМЕНИ\nКакое имя хочешь? Ответь мне, чтобы изменить.", event.callback_conv_msg_id, event.peer_id)
    elif chose == 2:
        bot.edit_message("СМЕНА ФАМИЛИИ\nКакую фамилию хочешь? Ответь мне, чтобы изменить.", event.callback_conv_msg_id, event.peer_id)
    elif chose == 3:
        bot.edit_message("У БОМЖА НЕДОСТАТОЧНО СРЕДСТВ", event.callback_conv_msg_id, event.peer_id)

@bot.on_reply_tag("шлепнуть", "шлёпнуть", "дать по жопе")
@eh.handle_exception(default_response=eh.automatic_response, conn_error=eh.connection_response)
def take_it(event):
    from random import choice
    
    user_1 = db.get_user(event.author_id)
    user_2 = db.get_user(event.reply_message[0])

    name_1 = user_1.name.capitalize()
    name_2 = user_2.name.capitalize()
    
    answers = [name_1 + " дал жёстко по жопе, что аж " + name_2 + " покраснел/а от стыда и злости. Дальше они целовались в засос."]
    answers.append(name_1 + " не смог попасть по жопе " + name_2 + ", из-за чего " + name_2 + " продырявил/а жопу " + name_1)
    
    bot.send_message(choice(answers), event.peer_id)

@bot.tag(bot.bot_name, "горк", "ГОРК", "Горк")
async def gork(event):
    rest_msg = "".join(event.message.split()[1:])
    content = await openrouter_api.api.async_query(rest_msg)
    think = content.rfind("</think>")
    if think != -1:
       content = content[think + len("</think>"):]        
    bot.send_message(content, event.peer_id)
    await openrouter_api.cleanup()

@bot.new_message
def init_chat(event):
    if not db.is_chat_existing(event.peer_id):
        members = bot.get_raw_conversation_members(event.peer_id)
        db.init_database(event.peer_id, members)
    
@bot.new_message
def increment_msg_count(event):
    if not db.get_user(event.author_id).is_empty():
        db.increment_msg_count(event.author_id, event.peer_id)
        db.add_coins(event.author_id, event.peer_id, 1)

@bot.new_message
def check_membership(event):
    if db.get_user_chat(event.author_id, event.peer_id).is_empty():
        user = bot.get_raw_conversation_member(event.author_id, event.peer_id)
        is_admin = user["is_admin"] if "is_admin" in user else False
        is_owner = user["is_admin"] if "is_admin" in user else False
        db.add_user(user["id"], user["last_name"], user["first_name"], event.peer_id, is_admin=is_admin, is_owner=is_owner)

@bot.comand("/активы")
@eh.handle_exception(default_response=eh.automatic_response, conn_error=eh.connection_response)
def top_users(event):
    
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

    
    mems = db.get_top_members(event.peer_id)
    ans = "🐒🦄 НАШИ ТОПОВЫЕ АКТИВЧИКИ ⭐\n\n"
    for i in range(min(len(mems), 10)):
        vk_id = mems[i].vk_id; msg_count = mems[i].msg_count
        person = db.get_user(vk_id)
        ans += fancy_top(i + 1, person.sec_name, person.name, msg_count)

    bot.send_message(ans, event.peer_id)

@bot.comand("/админы")
@eh.handle_exception(default_response=eh.automatic_response, conn_error=eh.connection_response)
def admins(event):
    mems = db.get_admin_members(event.peer_id)
    ans = "Список админов\n\n"
    for i in range(len(mems)):
        vk_id = mems[i].vk_id
        person = db.get_user(vk_id)
        ans += f"{i + 1}. {person.name} {person.sec_name}\n"
    
    bot.send_message(ans, event.peer_id)

@bot.comand("/основатель")
@eh.handle_exception(default_response=eh.automatic_response, conn_error=eh.connection_response)
def owner(event):
    owner = db.get_owner(event.peer_id)
    if owner is None:
        bot.send_message("Основателем является паблик", event.peer_id)
        return
        
    ans = "Основатель: "
    vk_id = owner.vk_id
    person = db.get_user(vk_id)
    ans += f"{person.name} {person.sec_name}"
    
    bot.send_message(ans, event.peer_id)

@bot.comand("кто я", "статы")
@eh.handle_exception(default_response=eh.automatic_response, conn_error=eh.connection_response)
def who_am_i(event):
    base_info = db.get_user(event.author_id)
    user_chat_info = db.get_user_chat(event.author_id, event.peer_id)

    ans = "СТАТЫ\n"
    ans += "👀Информация об " + base_info.name + " " + base_info.sec_name
    ans += "\n\nНаписал сообщений " + str(user_chat_info.msg_count)
    if user_chat_info.is_owner:
        ans += "\nЯвляется основателем!!!✍"
    else: ans += "\nНе является основателем...😪"
    if user_chat_info.is_admin:
        ans += "\nЯвляется админчиком!!!🤩"
    else: ans += "\nНе является админом...😰"
    ans += "\nИмеет " + str(db.get_coins(event.author_id, event.peer_id)) + " сатоши"
    ans += "\n\nСменить имя. Цена 1000 сатоши"
    ans += "\nСменить фамилию. Цена 1000 сатоши"
    ans += "\nСТАТЬ ВИП. ЦЕНА 100000 САТОШИ"

    kbd = Keyboard(inline=True)
    kbd.add_callback_button("Сменить имя", color=ButtonColor.PRIMARY, payload={"callback_type": CallbackType.MARKET, "chose": 1})
    kbd.add_line()
    kbd.add_callback_button("Сменить фамилию", color=ButtonColor.PRIMARY, payload={"callback_type": CallbackType.MARKET, "chose": 2})
    kbd.add_line()
    kbd.add_callback_button("Стать вип", color=ButtonColor.PRIMARY, payload={"callback_type": CallbackType.MARKET, "chose": 3})
    
    bot.send_message(ans, event.peer_id, keyboard=kbd.get_keyboard())

@bot.on_reply_tag("кто ты", "кто ты такой", "кто есть", "какая масть")
@eh.handle_exception(default_response=eh.automatic_response, conn_error=eh.connection_response)
def who_are_you(event):
    if db.get_user(event.reply_message[0]).is_empty():
        return
    
    author_id = event.reply_message[0]
    if author_id < 0:
        bot.send_message("Ты че до паблика доебался", event.peer_id)
        return
    
    base_info = db.get_user(author_id)
    user_chat_info = db.get_user_chat(author_id, event.peer_id)
    
    ans = ""
    ans += "👀Информация об " + base_info.name + " " + base_info.sec_name
    ans += "\n\nНаписал сообщений " + str(user_chat_info.msg_count)
    if user_chat_info.is_owner:
        ans += "\nЯвляется основателем!!!✍"
    else: ans += "\nНе является основателем...😪"
    if user_chat_info.is_admin:
        ans += "\nЯвляется админчиком!!!🤩"
    else: ans += "\nНе является админом...😰"
    ans += "\nИмеет " + str(db.get_coins(event.reply_message[0], event.peer_id)) + " сатоши"
    
    bot.send_message(ans, event.peer_id)
        
@bot.tag("ньюсач", "топор", "униан", "поздняков", "баебы", "баёбы") # TODO: fix index issue
@eh.handle_exception(default_response=eh.automatic_response, conn_error=eh.connection_response)
async def send_tg_post(event):
    msg_list = event.message.lower().split()
    tag = msg_list[0]
    arg = msg_list[1] if len(msg_list) > 1 else None

    index = 0
    is_rand = False

    if arg is None:
        pass
    elif arg.isnumeric():
        index = int(arg)
    elif arg == "рандом":
        is_rand = True
    else:
        bot.send_message("Был передан неизвестный аргумент. Динаху.", event.peer_id)
        return
    
    post = ""
    if tag == "ньюсач":
        post = await tg.get_post("ru2ch", index, is_rand)
    elif tag == "униан":
        post = await tg.get_post("uniannet", index, is_rand)
    elif tag == "баебы" or tag == "баёбы":
        post = await tg.get_post("dolbaepiss", index, is_rand)
    elif tag == "топор":
        post = await tg.get_post(tg.convert_id(1237513492), index, is_rand)
    elif tag == "поздняков":
        post = await tg.get_post(tg.convert_id(1732054517), index, is_rand)
    
    bot.send_message(post[0], event.peer_id, media_dir=post[1])

@bot.tag("sql")
@eh.handle_exception(default_response=eh.automatic_response, conn_error=eh.connection_response)
def sql(event):
    if event.author_id == 766134059:
        rest_msg = event.message[len("sql")+1:]
        bot.send_message(str(db.query(rest_msg)), event.peer_id)

@bot.new_message
@throttle(interval_seconds=5.0)
@eh.handle_exception(default_response=eh.automatic_response, conn_error=eh.connection_response)
async def process_yt(event):    
    from urllib.parse import urlparse, parse_qs, urlencode
    from urllib.request import urlopen
    from bs4 import BeautifulSoup
    import re
    
    def video_id(value):
        query = urlparse(value)
        if query.hostname == 'youtu.be':
            return query.path[1:]
        if query.hostname in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
            if query.path == '/watch':
                p = parse_qs(query.query)
                return p['v'][0]
            if query.path[:7] == '/embed/':
                return query.path.split('/')[2]
            if query.path[:3] == '/v/':
                return query.path.split('/')[2]
            if query.path[:8] == '/shorts/':
                return query.path.split('/')[2]
        return None

    def get_title(url: str):
        with urlopen(url) as response:
            response_text = response.read()
            data = response_text.decode()
            soup = BeautifulSoup(data, features="html.parser")
            title = soup.find_all(name="title")[0].text
            return title

    def download_image(url, vid):
        import os
        filename = os.getcwd() + "/" + vid + '.png'
        
        with urlopen(url) as response:
            f = open(filename, mode='wb')
            f.write(response.read())
            f.close()
        return filename
    
    msg = event.message
    url = re.search(r"(?P<url>https?://[^\s]+)", msg)
    if url != None and video_id(url.group("url")) != None:
        url = url.group("url")
        vid = video_id(url)

        title = get_title("https://www.youtube.com/watch?v=" + vid)
        filename = download_image("https://img.youtube.com/vi/" + vid + "/hqdefault.jpg", vid)

        bot.send_message(title, event.peer_id, media_dir=[filename])

    
if __name__ == "__main__":
    bot.run_forever()
