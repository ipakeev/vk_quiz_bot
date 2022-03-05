import json
import typing
from typing import Optional

from app.store.vk_api.keyboard import Keyboard, Carousel
from app.store.vk_api.responses import VKUser
from app.store.game.payload import BasePayload, PayloadFactory, EmptyPayload

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BaseEvent:
    chat_id: int
    payload: BasePayload

    def __init__(self, app: "Application"):
        self.app = app
        self.states = app.store.states
        self.games = app.store.games
        self.quiz = app.store.quiz

    async def send_sticker(self, sticker_id: int) -> bool:
        return await self.app.store.vk_messenger.send_sticker(self.chat_id, sticker_id)

    async def send(self,
                   message: str,
                   photo: Optional[str] = None,
                   keyboard: Optional[Keyboard] = None,
                   carousel: Optional[Carousel] = None) -> bool:
        self.states.set_previous_text(self.chat_id, message)
        return await self.app.store.vk_messenger.send(
            self.chat_id,
            message,
            photo=photo,
            keyboard=keyboard,
            carousel=carousel,
        )


class ChatInviteRequest(BaseEvent):

    def __init__(self, data: dict, app: "Application"):
        super(ChatInviteRequest, self).__init__(app)
        self.chat_id = data["object"]["message"]["peer_id"]
        self.payload = EmptyPayload()


class BaseMessageEvent(BaseEvent):
    event_id: str
    conversation_message_id: int
    user_id: int

    async def get_user_info(self) -> Optional[VKUser]:
        return await self.app.store.vk_messenger.get_user_info(self.user_id)

    async def edit(self,
                   message: str,
                   photo: Optional[str] = None,
                   keyboard: Optional[Keyboard] = None,
                   carousel: Optional[Carousel] = None) -> bool:
        self.states.set_previous_text(self.chat_id, message)
        return await self.app.store.vk_messenger.edit(
            self.chat_id,
            self.conversation_message_id,
            message,
            photo=photo,
            keyboard=keyboard,
            carousel=carousel,
        )

    async def delete(self) -> bool:
        return await self.app.store.vk_messenger.delete(self.chat_id, self.conversation_message_id)


class MessageText(BaseMessageEvent):

    def __init__(self, data: dict, app: "Application"):
        super(MessageText, self).__init__(app)
        body = data["object"]["message"]
        self.chat_id: int = body["peer_id"]
        self.event_id: str = data["event_id"]  # в корне data
        self.conversation_message_id: int = body["conversation_message_id"]
        self.user_id: int = body["from_id"]
        self.text: str = body["text"]
        self.date: int = body["date"]

        payload = body.get("payload")  # empty payload returns as [] :-/
        if payload:  # and returns as json :-/
            payload = json.loads(payload)
        payload = payload or {}
        self.payload: BasePayload = PayloadFactory.create(payload)


class MessageCallback(BaseMessageEvent):

    def __init__(self, data: dict, app: "Application"):
        super(MessageCallback, self).__init__(app)
        body = data["object"]
        self.chat_id: int = body["peer_id"]
        self.event_id: str = body["event_id"]  # в поле object
        self.conversation_message_id: int = body["conversation_message_id"]
        self.user_id: int = body["user_id"]
        self.payload: BasePayload = PayloadFactory.create(
            body.get("payload") or {}  # empty payload returns as [] :-/
        )

    async def event_ok(self) -> bool:
        return await self.app.store.vk_messenger.event_ok(self.chat_id, self.user_id, self.event_id)

    async def show_snackbar(self, message: str) -> bool:
        return await self.app.store.vk_messenger.show_snackbar(self.chat_id, self.user_id, self.event_id, message)
