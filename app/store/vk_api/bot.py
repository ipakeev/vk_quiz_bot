import typing
from collections.abc import Callable, Awaitable
from dataclasses import dataclass
from functools import wraps
from typing import Optional, Union

from app.base.accessor import BaseAccessor
from app.store.vk_api import events
from app.store.vk_api.events import BaseEvent
from app.store.vk_api.keyboard import Keyboard, CallbackButton, ButtonColor
from app.store.vk_api.responses import ConversationMembersResponse

if typing.TYPE_CHECKING:
    from app.web.app import Application


@dataclass
class Subscriber:
    condition: Optional[Callable[[BaseEvent], bool]]
    func: Callable[[BaseEvent], Awaitable[None]]


def dummy_condition(_: BaseEvent) -> bool:
    return True


class VKBot(BaseAccessor):

    def __init__(self, app: "Application"):
        super(VKBot, self).__init__(app)
        self._chat_invite_request_subscribers: list[Subscriber] = []
        self._message_text_subscribers: list[Subscriber] = []
        self._message_callback_subscribers: list[Subscriber] = []

    def on_chat_invite_request(self, condition: Optional[Callable[[BaseEvent], bool]] = None):
        condition = condition or dummy_condition

        def decorator(func: Callable[[BaseEvent], Awaitable[None]]):
            self._chat_invite_request_subscribers.append(
                Subscriber(condition=condition, func=func)
            )

            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    def on_message_text(self, condition: Optional[Callable[[BaseEvent], bool]] = None):
        condition = condition or dummy_condition

        def decorator(func: Callable[[BaseEvent], Awaitable[None]]):
            self._message_text_subscribers.append(
                Subscriber(condition=condition, func=func)
            )

            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    def on_message_callback(self, condition: Optional[Callable[[BaseEvent], bool]] = None):
        condition = condition or dummy_condition

        def decorator(func: Callable[[BaseEvent], Awaitable[None]]):
            self._message_callback_subscribers.append(
                Subscriber(condition=condition, func=func)
            )

            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    async def handle_event(self, event: BaseEvent) -> None:
        if isinstance(event, events.ChatInviteRequest):
            for subscriber in self._chat_invite_request_subscribers:
                if subscriber.condition(event):
                    return await subscriber.func(event)
        elif isinstance(event, events.MessageText):
            for subscriber in self._message_text_subscribers:
                if subscriber.condition(event):
                    return await subscriber.func(event)
        elif isinstance(event, events.MessageCallback):
            for subscriber in self._message_callback_subscribers:
                if subscriber.condition(event):
                    return await subscriber.func(event)
        else:
            self.app.logger.warning(f"unknown event: {event}")


class GameCommands:
    start = "start"
    stop = "stop"


def register_bot_actions(bot: VKBot):
    keyboard_start = Keyboard(inline=True, buttons=[
        [CallbackButton("😍 start", payload={"action": GameCommands.start}, color=ButtonColor.green)],
    ])
    keyboard_stop = Keyboard(inline=True, buttons=[
        [CallbackButton("😎 stop", payload={"action": GameCommands.stop}, color=ButtonColor.red)],
    ])

    def bot_is_admin(members: Optional[ConversationMembersResponse]) -> bool:
        if not members:
            return False
        # Для сообщества: -id сообщества
        group_id_as_member = -bot.app.config.vk_bot.group_id
        return group_id_as_member in members.admin_ids

    @bot.on_chat_invite_request()
    async def invited(msg: events.ChatInviteRequest):
        await msg.send("Привет. Я - бот для игры в викторину.\n"
                       "Перед началом игры необходимо назначить меня администратором беседы.\n"
                       "Как всё будет готово - нажимай на кнопку.",
                       keyboard=keyboard_start)

    @bot.on_message_text(lambda i: i.text.lower() == GameCommands.start)
    @bot.on_message_callback(lambda i: i.payload.get("action") == GameCommands.start)
    async def start(msg: Union[events.MessageText, events.MessageCallback]):
        members = await msg.app.store.vk_messenger.get_conversation_members(msg.peer_id)
        if not bot_is_admin(members):
            await msg.send("Без прав администратора беседы я не смогу начать игру.")
            return

        await msg.app.store.games.create_game(msg.peer_id, members)

        if isinstance(msg, events.MessageText):
            await msg.send("Для остановки игры нажми на кнопку", keyboard=keyboard_stop)
        else:
            await msg.edit("Для остановки игры нажми на кнопку", keyboard=keyboard_stop)

        await msg.send("Поехали")

    @bot.on_message_text(lambda i: i.text.lower() == GameCommands.stop)
    @bot.on_message_callback(lambda i: i.payload.get("action") == GameCommands.stop)
    async def stop(msg: Union[events.MessageText, events.MessageCallback]):
        if isinstance(msg, events.MessageCallback):
            await msg.edit("Для начала игры нажми на кнопку", keyboard=keyboard_start)
        await msg.send("Результаты")
