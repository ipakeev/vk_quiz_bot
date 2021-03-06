import asyncio
import typing
from dataclasses import dataclass
from functools import wraps

from aiohttp import ClientSession, TCPConnector

from app.base.accessor import BaseAccessor

if typing.TYPE_CHECKING:
    from app.web.app import Application


def build_query(host: str, method: str, params: dict) -> str:
    url = host + method + "?"
    if "v" not in params:
        params["v"] = "5.131"
    url += "&".join([f"{k}={v}" for k, v in params.items()])
    return url


@dataclass
class PollServiceConfig:
    key: str
    server: str
    ts: str


def catch(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        self: VKLongPoller = args[0]
        while 1:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                self.app.logger.warning(e)
                await asyncio.sleep(5.0)

    return wrapper


class VKLongPoller(BaseAccessor):
    API_PATH = "https://api.vk.com/method/"

    session: ClientSession
    poll_service_config: PollServiceConfig

    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.poller = LongPollingLoop(app)

    async def connect(self, app: "Application"):
        # force_close to avoid errors with close connection
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False, force_close=True))
        await self.init_long_poll_service()
        await self.poller.start_polling()

    async def disconnect(self, app: "Application"):
        await self.poller.stop_polling()
        await self.session.close()

    @catch
    async def init_long_poll_service(self):
        url = build_query(host=self.API_PATH,
                          method="groups.getLongPollServer",
                          params={
                              "group_id": self.app.config.vk_bot.group_id,
                              "access_token": self.app.config.vk_bot.token,
                          })
        async with self.session.get(url) as resp:
            data = (await resp.json())["response"]
            self.poll_service_config = PollServiceConfig(key=data["key"],
                                                         server=data["server"],
                                                         ts=data["ts"])

    @catch
    async def query_long_poll(self):
        url = build_query(host=self.poll_service_config.server,
                          method="",
                          params={
                              "act": "a_check",
                              "key": self.poll_service_config.key,
                              "ts": self.poll_service_config.ts,
                              "wait": self.app.config.vk_bot.long_poller_wait,
                          })
        async with self.session.get(url) as resp:
            data = await resp.json()
            if "ts" in data:
                self.poll_service_config.ts = data["ts"]
                for update in data.get("updates", []):
                    await self.app.store.vk_updates_queue.put(update)
            else:
                # failed
                await self.init_long_poll_service()


class LongPollingLoop:
    long_poll_task: asyncio.Task

    def __init__(self, app: "Application"):
        self.app = app
        self.is_running = False

    async def start_polling(self):
        self.app.logger.info("start polling")
        self.is_running = True
        self.long_poll_task = asyncio.create_task(self.long_polling())

    async def stop_polling(self):
        self.app.logger.info("stop polling")
        self.is_running = False
        await self.long_poll_task

    async def long_polling(self):
        while self.is_running:
            await self.app.store.vk_long_poller.query_long_poll()
