import random
import typing

from aiohttp import ClientSession, TCPConnector

from app.database.accessor import BaseAccessor
from app.store.vk_api.long_poller import build_query

if typing.TYPE_CHECKING:
    from app.web.app import Application


class VKMessenger(BaseAccessor):
    API_PATH = "https://api.vk.com/method/"

    session: ClientSession

    async def connect(self, app: "Application"):
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))

    async def disconnect(self, app: "Application"):
        await self.session.close()

    async def send(self, params: dict, text: str, keyboard=None, inline=False):
        async with self.session.get(
                build_query(
                    self.API_PATH,
                    "messages.send",
                    params={
                        **params,
                        "random_id": random.randint(1, 2 ** 32),
                        "message": text,
                        "access_token": self.app.config.vk_bot.token,
                    },
                )

        ) as resp:
            data = await resp.json()
            self.app.logger.debug(data)

    async def edit(self):
        pass

    async def delete(self):
        pass

    async def chat_info(self):
        pass

    async def chat_users(self):
        pass

    async def user_info(self):
        pass
