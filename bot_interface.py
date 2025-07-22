import db
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotMessageEvent, VkBotEventType
from config import GROUP_TOKEN, GROUP_ID

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

from dataclasses import dataclass
from collections.abc import Callable
from types import CoroutineType
from enum import Enum

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
            return (self.event.message["reply_message"]["from_id"], self.event.message["reply_message"]["text"])
        return ()
    
    @property
    def message(self) -> str:
        return self.event.message["text"]

    @property
    def author_id(self) -> str:
        return self.event.message["from_id"]

    @property
    def peer_id(self) -> int:
        return self.event.message["peer_id"]


class ComandType(Enum):
    IS_TAG = 1
    IS_COMAND = 2
    NEW_MESSAGE = 3
    ON_REPLY = 4
    
@dataclass
class Comand:
    comand_type: ComandType
    msg: str
    doer: Callable | CoroutineType

class Bot:
    def __init__(self):
        self._comands: List[Comand] = []
        
        self._queue = asyncio.Queue()
        self._loop = None
        self._executor = ThreadPoolExecutor(max_workers=10)
        
        self._session = vk_api.VkApi(token=GROUP_TOKEN)
        self._longpoll = LongPoll(self._session, GROUP_ID)

    def run_forever(self):
        asyncio.run(self._work_around())
        
    async def _work_around(self):
        self._loop = asyncio.get_running_loop()
        thread = threading.Thread(target=self.listen, daemon=True)
        thread.start()

        while True:
            event = await self._queue.get()
            asyncio.create_task(self._process_comands(event))

    async def _process_comands(self, event: BotEvent):
        for i in self._comands:
            i.msg = self.parse_name(i.msg)
            await self._comand_iterate(event, i)

    def parse_name(self, arg):
        if isinstance(arg, tuple):
            l = []
            for i in range(len(arg)):
                l.append(arg[i].replace(self.bot_name, "gork"))
            return tuple(l)
        else:
            return arg.replace(self.bot_name, "gork")

    @property
    def bot_name(self):
        return "$210000(NAME_OF_BOT)"
        
    async def _comand_iterate(self, event: BotEvent, comand: ComandType):
        async def call(callee):
            if asyncio.iscoroutine(callee):
                await callee
        
        match comand.comand_type:
            case ComandType.IS_COMAND:
                if event.message.lower() == comand.msg:
                    await call(comand.doer(event))
            case ComandType.IS_TAG:
                if any([event.message.lower().startswith(i) for i in comand.msg]):
                    await call(comand.doer(event))
            case ComandType.ON_REPLY:
                if len(event.reply_message) != 0:
                    await call(comand.doer(event))
            case ComandType.NEW_MESSAGE:
                await call(comand.doer(event))
                        
    def listen(self):
        for event in self.get_event():
            asyncio.run_coroutine_threadsafe(self._queue.put(event), self._loop)
        
    def get_event(self):
        for i in self._longpoll.listen():
            yield BotEvent(i)
            
    def get_raw_conversation_members(self, peer_id):
        if not isinstance(peer_id, int):
            raise ValueError("Restricted type")
        
        return self._session.method("messages.getConversationMembers", {"peer_id": peer_id})

    def get_upload_photo(self, direc: str) -> dict:
        upload = vk_api.VkUpload(self._session)
        temp = upload.photo_messages(direc)[0]
        
        return "photo" + str(temp["owner_id"]) + "_" + str(temp["id"])
    
    def send_message(self, msg, peer_id, photo_dir=""):
        if not isinstance(msg, str) or not isinstance(peer_id, int) or not isinstance(photo_dir, str):
            raise ValueError("Restricted type")
        if msg == "":
            msg = "Пустое сообщение"

        if photo_dir != "":
            photo_dir = self.get_upload_photo(photo_dir)

        params = {
            "peer_id": peer_id,
            "random_id": 0,
            "message": msg,
            "attachment": photo_dir
        }
                
        self._session.method("messages.send", params)

    def comand(self, raw_msg: str):
        def decorator(func):
            self._comands.append(Comand(comand_type=ComandType.IS_COMAND, msg=raw_msg, doer=func))
            return func
        return decorator

    def tag(self, *args):
        def decorator(func):
            self._comands.append(Comand(comand_type=ComandType.IS_TAG, msg=args, doer=func))
            return func
        return decorator

    def new_message(self, func): # decorator
        self._comands.append(Comand(comand_type=ComandType.NEW_MESSAGE, msg="", doer=func))
        return func

    def on_reply(self, func): # decorator
        self._comands.append(Comand(comand_type=ComandType.ON_REPLY, msg="", doer=func))
        return func

    
class LongPoll(VkBotLongPoll):
    def listen(self):
        while True:
            try:
                for event in self.check():
                    yield event
            except Exception as e:
                print(e)
