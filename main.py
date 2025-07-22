from bot_interface import Bot
import error_handle as eh
import openrouter_api
import db, tg

bot = Bot()

@bot.comand("старт")
def hello(event):
    bot.send_message("Привет", event.peer_id)

@bot.tag(bot.bot_name, "горк", "ГОРК")
async def gork(event):
    rest_msg = "".join(event.message.split()[1:])
    content = await openrouter_api.api.async_query(rest_msg)
    bot.send_message(content, event.peer_id)
    await openrouter_api.cleanup()

@bot.new_message
def init_chat(event):
    if not db.is_chat_existing(event.peer_id):
        members = bot.get_raw_conversation_members(event.peer_id)
        db.init_database(event.peer_id, members)
    
@bot.new_message
def increment_msg_count(event):
    db.increment_msg_count(event.author_id, event.peer_id)

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

@bot.comand("кто я")
@eh.handle_exception(default_response=eh.automatic_response, conn_error=eh.connection_response)
def who_am_i(event):
    base_info = db.get_user(event.author_id)
    user_chat_info = db.get_user_chat(event.author_id, event.peer_id)

    ans = ""
    ans += "👀Информация об " + base_info.sec_name + " " + base_info.name
    ans += "\n\nНаписал сообщений " + str(user_chat_info.msg_count)
    if user_chat_info.is_owner:
        ans += "\nЯвляется основателем!!!✍"
    else: ans += "\nНе является основателем...😪"
    if user_chat_info.is_admin:
        ans += "\nЯвляется админчиком!!!🤩"
    else: ans += "\nНе является админом...😰"
    
    bot.send_message(ans, event.peer_id)

@bot.on_reply
@eh.handle_exception(default_response=eh.automatic_response, conn_error=eh.connection_response)
def who_are_you(event):
    author_id = event.reply_message[0]
    if author_id < 0:
        bot.send_message("Ты че до паблика доебался", event.peer_id)
        return
    
    if event.message.lower() == "кто ты":
        base_info = db.get_user(author_id)
        user_chat_info = db.get_user_chat(author_id, event.peer_id)

        ans = ""
        ans += "👀Информация об " + base_info.sec_name + " " + base_info.name
        ans += "\n\nНаписал сообщений " + str(user_chat_info.msg_count)
        if user_chat_info.is_owner:
            ans += "\nЯвляется основателем!!!✍"
        else: ans += "\nНе является основателем...😪"
        if user_chat_info.is_admin:
            ans += "\nЯвляется админчиком!!!🤩"
        else: ans += "\nНе является админом...😰"
        
        bot.send_message(ans, event.peer_id)
        
@bot.tag("ньюсач", "топор", "униан", "поздняков", "баебы", "баёбы")
@eh.handle_exception(default_response=eh.automatic_response, conn_error=eh.connection_response)
async def send_tg_post(event):
    msg_list = event.message.split()
    tag = msg_list[0]
    arg = msg_list[1]

    index = 1
    is_rand = False
    
    if arg.isnumeric():
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
    
    bot.send_message(post, event.peer_id)
    
if __name__ == "__main__":
    bot.run_forever()
