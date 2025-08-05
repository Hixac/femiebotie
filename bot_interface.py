import db
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotMessageEvent, VkBotEventType
from config import GROUP_TOKEN, GROUP_ID

import json
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

from dataclasses import dataclass
from collections.abc import Callable
from types import CoroutineType
from enum import Enum

from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from parse_vk_markup import Parser

Keyboard = VkKeyboard
ButtonColor = VkKeyboardColor

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
    def callback_payload(self) -> str | dict | list | None:
        return self.event.object.payload

    @property
    def callback_event_id(self) -> str:
        return self.event.object.event_id

    @property
    def callback_conv_msg_id(self) -> int:
        return self.event.object.conversation_message_id
    
    @property
    def author_id(self) -> str:
        if not (self.event.message is None):
            return self.event.message["from_id"]
        else:
            return self.event.object.user_id

    @property
    def peer_id(self) -> int:
        if not (self.event.message is None):
            return self.event.message["peer_id"]
        else:
            return self.event.object.peer_id

class CallbackType:
    GAMBLING_GAME_GRAB = "GAMBLING_GAME_GRAB"
    GAMBLING_GAME_SHOW = "GAMBLING_GAME_SHOW"
    MARKET = "MARKET"
    
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
    ANY_CALLBACK = 10
    BY_CALLBACK_TYPE = 11
    
@dataclass
class Comand:
    comand_type: ComandType
    msg: str | int
    doer: Callable | CoroutineType
    args: tuple

class Bot:
    @property
    def bot_name(self):
        return "gork"

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
            if event.event_type == VkBotEventType.MESSAGE_NEW:
                await self._comand_iterate(event, i)
            elif event.event_type == VkBotEventType.MESSAGE_EVENT:
                await self._callback_iterate(event, i)

    async def _callback_iterate(self, event: BotEvent, comand: Comand):
        async def call(callee):
            if asyncio.iscoroutine(callee):
                await callee

        def is_callback_type_correct(callback_type):
            payload = event.callback_payload
            return not (payload is None) and "callback_type" in payload and payload["callback_type"] == callback_type

        match comand.comand_type:
            case ComandType.ANY_CALLBACK:
                await call(comand.doer(event))
            case ComandType.BY_CALLBACK_TYPE:
                if is_callback_type_correct(comand.msg):
                    await call(comand.doer(event))
            case _:
                return
    
    async def _comand_iterate(self, event: BotEvent, comand: Comand):
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

    # def get_upload_video(self, direc: str) -> dict:
    #     upload = vk_api.VkUpload(self._session)
    #     temp = upload.video(direc)[0]
    #
    #     return "video" + str(temp["owner_id"]) + "_" + str(temp["id"])
    
    def get_upload_photo(self, direc: str) -> dict:
        upload = vk_api.VkUpload(self._session)
        temp = upload.photo_messages(direc)[0]
        
        return "photo" + str(temp["owner_id"]) + "_" + str(temp["id"])

    def preset_open_link(self, url):
        if not isinstance(url, str):
            return ValueError("Restricted type")
        return {"type": "open_link", "link": url}
    
    def preset_show_snackbar(self, text):
        if not isinstance(text, str):
            return ValueError("Restricted type")
        return {"type": "show_snackbar", "text": text}

    def edit_message(self, msg, conv_msg_id, peer_id, keyboard={}):
        if not isinstance(msg, str) or not isinstance(peer_id, int):
            raise ValueError("Restricted type")
        if msg == "":
            msg = "Пустое сообщение"

        params = {
            "peer_id": peer_id,
            "conversation_message_id": conv_msg_id,
            "message": msg
        }

        if keyboard:
            params["keyboard"] = keyboard
            
        self._session.method("messages.edit", params)
    
    def send_event(self, event_id, user_id, peer_id, event_data):
        event_data = json.dumps(event_data)
        
        params = {
            "event_id": event_id,
            "user_id": user_id,
            "peer_id": peer_id,
            "event_data": event_data
        }

        self._session.method("messages.sendMessageEventAnswer", params)
    
    def send_message(self, msg, peer_id, media_dir="", keyboard={}, reply_to=0):
        if not isinstance(msg, str) or not isinstance(peer_id, int) or not isinstance(media_dir, str):
            raise ValueError("Restricted type")
        if msg == "":
            msg = "Пустое сообщение"


        if len(msg) > 4096:
            from math import floor
            for i in range(floor(len(msg) / 4096)):
                self.send_message(msg[i * 4096:min((i + 1) * 4096, len(msg))], peer_id, media_dir, keyboard, reply_to)
            return
            

        parser = Parser(msg)
        format_data = parser.parse()
        msg = parser.formatted_text

        
        params = {
            "peer_id": peer_id,
            "random_id": 0,
            "message": msg,
        }

        if keyboard:
            params["keyboard"] = keyboard
        if media_dir:
            if "mp4" in media_dir:
                print("Method is unavailable with group auth.")
            else:
                media_dir = self.get_upload_photo(media_dir)
                params["attachment"] = media_dir
        if reply_to != 0:
            params["reply_to"] = reply_to
        if format_data is not None:
            params["format_data"] = format_data
            
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
    
    def any_callback(self, func): # decorator
        self._comands.append(Comand(comand_type=ComandType.ANY_CALLBACK, msg="", args=(), doer=func))
        return func

    def by_callback_type(self, callback_type = 0):
        if callback_type == 0:
            raise ValueError("No type specified")
        
        def decorator(func):
            self._comands.append(Comand(comand_type=ComandType.BY_CALLBACK_TYPE, msg=callback_type, args=(), doer=func))
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
