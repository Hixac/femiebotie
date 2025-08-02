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
        return self.event.message["text"] if not (self.event is None) else ""

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
    ON_REPLY_TAG = 5
    HEADER = 6
    HEADER_TAG = 7
    HEADER_COMAND = 8
    IS_TAG_ARGUMENTED = 9
    
@dataclass
class Comand:
    comand_type: ComandType
    msg: str | int
    doer: Callable | CoroutineType
    args: tuple

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
            await self._comand_iterate(event, i)

    @property
    def bot_name(self):
        return "gork"
        
    async def _comand_iterate(self, event: BotEvent, comand: ComandType):
        async def call(callee):
            if asyncio.iscoroutine(callee):
                await callee

        def is_comand(args):
            return any([event.message.lower() == i for i in args])
                
        def is_tag_there(args):
            return any([event.message.lower().startswith(i) for i in args])
                
        def is_reply_message_correct():
            return len(event.reply_message) != 0 and event.reply_message[0] == -int(GROUP_ID)

        def is_header_correct(head):
            return is_reply_message_correct() and event.reply_message[1][:len(head)] == head

        def is_arguments_correct(tags, count_args):
            if count_args == 0: return True

            msg = event.message.lower()
            for i in tags:
                f = msg.find(i)
                if f == 0:
                    msg = msg[len(i):]
                    break
                
            msg = msg.split()
            if len(msg) == count_args:
                return True
            return False
        
        match comand.comand_type:
            case ComandType.IS_COMAND:
                if is_comand(comand.args):
                    await call(comand.doer(event))
            case ComandType.IS_TAG:
                if is_tag_there(comand.args) and is_arguments_correct(comand.args, comand.msg):
                    await call(comand.doer(event))
            case ComandType.ON_REPLY:
                if len(event.reply_message) != 0:
                    await call(comand.doer(event))
            case ComandType.ON_REPLY_TAG:
                if len(event.reply_message) != 0 and is_tag_there(comand.args):
                    await call(comand.doer(event))
            case ComandType.NEW_MESSAGE:
                await call(comand.doer(event))
            case ComandType.HEADER:
                if is_header_correct(comand.msg):
                    await call(comand.doer(event))
            case ComandType.HEADER_TAG:
                if is_header_correct(comand.msg) and is_tag_there(comand.args):
                    await call(comand.doer(event))
            case ComandType.HEADER_COMAND:
                if is_header_correct(comand.msg) and is_comand(comand.args):
                    await call(comand.doer(event))
                    
    def listen(self):
        for event in self.get_event():
            asyncio.run_coroutine_threadsafe(self._queue.put(event), self._loop)
        
    def get_event(self):
        for i in self._longpoll.listen():
            yield BotEvent(i)

    def get_raw_conversation_member(self, vk_id, peer_id): # no err handling
        if not isinstance(vk_id, int) or not isinstance(peer_id, int):
            raise ValueError("Restricted type")

        mbrs = self.get_raw_conversation_members(peer_id) 
        l = [i for i in mbrs['items'] if vk_id == i["member_id"]]
        misc =  self._session.method("users.get", {"user_ids": vk_id})
        
        return l[0] | misc[0]
            
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

    def comand(self, *args):
        def decorator(func):
            self._comands.append(Comand(comand_type=ComandType.IS_COMAND, msg="", args=args, doer=func))
            return func
        return decorator

    def tag(self, *args, take_args=0):
        def decorator(func):
            self._comands.append(Comand(comand_type=ComandType.IS_TAG, msg=take_args, args=args, doer=func))
            return func
        return decorator
    
    def new_message(self, func): # decorator
        self._comands.append(Comand(comand_type=ComandType.NEW_MESSAGE, msg="", args=(), doer=func))
        return func

    def on_reply(self, func): # decorator
        self._comands.append(Comand(comand_type=ComandType.ON_REPLY, msg="", args=(), doer=func))
        return func

    def on_reply_tag(self, *args):
        def decorator(func):
            self._comands.append(Comand(comand_type=ComandType.ON_REPLY_TAG, msg="", args=args, doer=func))
            return func
        return decorator

    def header(self, head: str = ""): # decorator
        if head == "":
            raise ValueError("No header specified")
        
        def decorator(func):
            self._comands.append(Comand(comand_type=ComandType.HEADER, msg=head, args=(), doer=func))
            return func
        return decorator

    def header_tag(self, head: str = "", *args): # decorator
        if head == "":
            raise ValueError("No header specified")
        
        def decorator(func):
            self._comands.append(Comand(comand_type=ComandType.HEADER_TAG, msg=head, args=args, doer=func))
            return func
        return decorator

    def header_comand(self, head: str = "", *args): # decorator
        if head == "":
            raise ValueError("No header specified")
        
        def decorator(func):
            self._comands.append(Comand(comand_type=ComandType.HEADER_TAG, msg=head, args=args, doer=func))
            return func
        return decorator

    
    
class LongPoll(VkBotLongPoll):
    def listen(self):
        while True:
            try:
                for event in self.check():
                    yield event
            except Exception as e:
                print(e)
