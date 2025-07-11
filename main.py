import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotMessageEvent, VkBotEventType
import comand

from config import GROUP_TOKEN, GROUP_ID

class BotEvent:
    def __init__(self, event: VkBotMessageEvent):
        self.event = event

    @property
    def event_type(self) -> VkBotEventType:
        return self.event.type

    @property
    def reply_message(self) -> str:
        if "reply_message" in self.event.message:
            return self.event.message["reply_message"]["text"]
        return ""
    
    @property
    def message(self) -> str:
        return self.event.message["text"]

    @property
    def author_id(self) -> str:
        return self.event.message["from_id"]

    @property
    def peer_id(self) -> int:
        return self.event.message["peer_id"]

class LongPoll(VkBotLongPoll):
    def listen(self):
        while True:
            try:
                for event in self.check():
                    yield event
            except Exception as e:
                print(e)

class Bot:
    @property
    def last_event(self):
        return self._last_event
    
    def __init__(self):
        self._session = vk_api.VkApi(token=GROUP_TOKEN)
        self._longpoll = LongPoll(self._session, GROUP_ID)
        self._last_event = None
        
    def get_event(self):
        for i in self._longpoll.listen():
            self._last_event = BotEvent(i)
            yield BotEvent(i)

    def send_message(self, msg, peer_id):
        if not isinstance(msg, str) or not isinstance(peer_id, int):
            raise ValueError("Restricted type")
        if msg == "":
            msg = "Пустое сообщение"
        self._session.method("messages.send", {"peer_id": peer_id, "random_id": 0, "message": msg, "attachment": "" })
            
def process_input(event, bot):
    if not isinstance(event, BotEvent) or not isinstance(bot, Bot):
        raise ValueError("Restricted type")
    if event.event_type.value == "message_new":
        comand.tag(event.message, bot)
            
def main():
    bot = Bot()
    is_inited = False
    for e in bot.get_event():
        if not is_inited:
            is_inited = True
            continue
        process_input(e, bot)
                
if __name__ == "__main__":
    main()
