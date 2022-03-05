import asyncio
import typing

from app.base.accessor import BaseAccessor
from app.store.vk_api import events

if typing.TYPE_CHECKING:
    from app.web.app import Application


class EventType:
    chat_invite_user = "chat_invite_user"
    message_new = "message_new"
    message_event = "message_event"
    message_edit = "message_edit"


class VKUpdatesPoller(BaseAccessor):
    task: asyncio.Task

    def __init__(self, app: "Application"):
        super(VKUpdatesPoller, self).__init__(app)
        self.is_running = False

    async def connect(self, app: "Application"):
        self.is_running = True
        self.task = asyncio.create_task(self.queue_poller())

    async def disconnect(self, app: "Application"):
        self.is_running = False
        await self.task

    async def queue_poller(self):
        queue = self.app.store.vk_updates_queue
        while self.is_running:
            while not queue.empty():
                update = await queue.get()
                await self.handle_update(update)
            await asyncio.sleep(0.5)

    async def handle_update(self, update: dict):
        event_type = update.get("type")
        if event_type == EventType.message_new:
            if update["object"]["message"].get("action", {}).get("type") == EventType.chat_invite_user:
                event = events.ChatInviteRequest(update, self.app)
            else:
                event = events.MessageText(update, self.app)
        elif event_type == EventType.message_event:
            event = events.MessageCallback(update, self.app)
        elif event_type == EventType.message_edit:
            self.app.logger.debug("skip")
            return
        else:
            self.app.logger.warning(f"unknown update: {update}")
            return

        # нам не нужно дожидаться завершения обработки event'а
        asyncio.create_task(self.app.store.vk_bot.handle_event(event))
