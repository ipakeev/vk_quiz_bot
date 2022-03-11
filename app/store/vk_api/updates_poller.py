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
    tasks: list[asyncio.Task]
    gc_task: asyncio.Task

    def __init__(self, app: "Application"):
        super(VKUpdatesPoller, self).__init__(app)
        self.is_running = False

    async def connect(self, app: "Application"):
        self.app.logger.info("init vk updates poller")
        self.is_running = True
        self.tasks = [asyncio.create_task(self.queue_poller())]
        self.gc_task = asyncio.create_task(self.garbage_collector())

    async def disconnect(self, app: "Application"):
        self.app.logger.info("shutdown vk updates poller")
        self.is_running = False
        for task in self.tasks:
            if task.done() or task.cancelled():
                continue
            await task
        if not self.gc_task.done():
            await self.gc_task

    async def queue_poller(self):
        queue = self.app.store.vk_updates_queue
        seconds = self.app.config.vk_bot.updates_poller_queue_poller_sleep
        while self.is_running:
            while not queue.empty():
                update = await queue.get()
                await self.handle_update(update)
            await asyncio.sleep(seconds)

    async def garbage_collector(self):
        seconds = self.app.config.vk_bot.updates_poller_gc_sleep
        while self.is_running:
            self.tasks = [i for i in self.tasks if not (i.done() or i.cancelled())]
            await asyncio.sleep(seconds)

    async def handle_update(self, update: dict):
        event_type = update.get("type")
        self.app.logger.debug(update)
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

        # нам не нужно дожидаться завершения обработки event'а в этой функции,
        # но в случае дисконнекта всё же нужно дождаться
        task = asyncio.create_task(self.app.store.vk_bot.handle_event(event))
        self.tasks.append(task)
