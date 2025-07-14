import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotMessageEvent, VkBotEventType
import comand

from config import GROUP_TOKEN, GROUP_ID

class BotEvent:
    def __init__(self, event: VkBotMessageEvent):
        self.event = event

    @property
    def conversation_message_id(self):
        return self.event.message['id']
        
    @property
    def raw(self):
        return self.event
        
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

    def send_message(self, msg, peer_id, reply_id=0):
        if not isinstance(msg, str) or not isinstance(peer_id, int) or not isinstance(reply_id, int):
            raise ValueError("Restricted type")
        if msg == "":
            msg = "Пустое сообщение"
            
        params = {
            "peer_id": peer_id,
            "random_id": 0,
            "message": msg,
            "attachment": ""
        }
        
        if reply_id > 0:
            params["reply_to"] = reply_id
        
        self._session.method("messages.send", params)

class ThreadSafeBot:
    def __init__(self, bot: Bot, loop: asyncio.AbstractEventLoop, executor: ThreadPoolExecutor):
        self._bot = bot
        self._loop = loop
        self._executor = executor

    def send_message(self, msg: str, peer_id: int, reply_id: int = 0):
        self._loop.run_in_executor(self._executor, self._bot.send_message, msg, peer_id, reply_id)

def run_listener(queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
    bot_listener = Bot()
    for event in bot_listener.get_event():
        asyncio.run_coroutine_threadsafe(queue.put(event), loop)

async def process_input_async(event, safe_bot):
    await comand.tag(event, safe_bot)

async def main():
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    executor = ThreadPoolExecutor(max_workers=10)
    
    bot_sender = Bot()
    safe_bot = ThreadSafeBot(bot_sender, loop, executor)
    
    thread = threading.Thread(target=run_listener, args=(queue, loop), daemon=True)
    thread.start()
    
    first_event = await queue.get()
    print("Skipped first event")
    
    while True:
        event = await queue.get()
        asyncio.create_task(process_input_async(event, safe_bot))

if __name__ == "__main__":
    asyncio.run(main())
