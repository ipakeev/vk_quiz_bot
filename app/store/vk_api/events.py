import typing

from app.store.vk_api.keyboard import Keyboard

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BaseEvent:
    peer_id: int

    def __init__(self, app: "Application"):
        self.app = app

    async def send(self, message: str, keyboard: Keyboard = None) -> bool:
        return await self.app.store.vk_messenger.send(self.peer_id, message, keyboard=keyboard)


class BaseMessageEvent(BaseEvent):
    conversation_message_id: int

    async def edit(self, message: str, keyboard: Keyboard = None) -> bool:
        return await self.app.store.vk_messenger.edit(
            self.peer_id, self.conversation_message_id, message, keyboard=keyboard
        )


class ChatInviteRequest(BaseEvent):

    def __init__(self, data: dict, app: "Application"):
        super(ChatInviteRequest, self).__init__(app)
        self.peer_id = data["object"]["message"]["peer_id"]


class MessageText(BaseMessageEvent):

    def __init__(self, data: dict, app: "Application"):
        super(MessageText, self).__init__(app)
        body = data["object"]["message"]
        self.peer_id: int = body["peer_id"]
        self.conversation_message_id: int = body["conversation_message_id"]
        self.date: int = body["date"]
        self.from_id: int = body["from_id"]
        self.text: str = body["text"]
        self.payload: dict = body.get("payload", {})


class MessageCallback(BaseMessageEvent):

    def __init__(self, data: dict, app: "Application"):
        super(MessageCallback, self).__init__(app)
        body = data["object"]
        self.peer_id: int = body["peer_id"]
        self.conversation_message_id: int = body["conversation_message_id"]
        self.from_id: int = body["user_id"]
        self.payload: dict = body.get("payload", {})
