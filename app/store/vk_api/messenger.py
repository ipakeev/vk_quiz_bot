import json
import random
import typing
from typing import Optional

from aiohttp import ClientSession, TCPConnector

from app.base.accessor import BaseAccessor
from app.store.vk_api.keyboard import Keyboard
from app.store.vk_api.responses import ConversationMembersResponse

if typing.TYPE_CHECKING:
    from app.web.app import Application


class VKMessenger(BaseAccessor):
    API_PATH = "https://api.vk.com/method/"

    session: ClientSession

    async def connect(self, app: "Application"):
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))

    async def disconnect(self, app: "Application"):
        await self.session.close()

    def build_query_url(self, method: str, params: dict) -> str:
        params["access_token"] = self.app.config.vk_bot.token
        params["v"] = "5.131"
        return self.API_PATH + method + "?" + "&".join([f"{k}={v}" for k, v in params.items()])

    async def query(self, url: str, method="GET") -> dict:
        async with self.session.request(method, url) as resp:
            if resp.ok:
                data = await resp.json()
                self.app.logger.debug(f"status={resp.status}, method={method}")
                return data
            else:
                self.app.logger.warning(f"status={resp.status}, method={method}, url={url}")
                return {}

    async def send(self, peer_id: int, message: str, keyboard: Keyboard = None) -> bool:
        params = {
            "peer_id": peer_id,
            "random_id": random.randint(1, 2 ** 32),
            "message": message,
        }
        if keyboard:
            params["keyboard"] = json.dumps(keyboard.as_dict())

        url = self.build_query_url("messages.send", params)
        data = await self.query(url, method="POST")

        if data.get("response") is not None:
            self.app.logger.debug("msg sent")
            return True
        else:
            self.app.logger.warning(f"msg not sent ({params})")
            return False

    async def edit(self, peer_id: int, conversation_message_id: int, message: str, keyboard: Keyboard = None) -> bool:
        params = {
            "peer_id": peer_id,
            "conversation_message_id": conversation_message_id,
            "message": message,
        }
        if keyboard:
            params["keyboard"] = json.dumps(keyboard.as_dict())

        url = self.build_query_url("messages.edit", params)
        data = await self.query(url, method="POST")

        if data.get("response") == 1:
            self.app.logger.debug("msg edited")
            return True
        else:
            # {'error': {'error_code': 15, 'error_msg': 'Access denied'}}
            self.app.logger.info(f"msg not found ({params})")
            return False

    async def get_conversation_members(self, peer_id: int) -> Optional[ConversationMembersResponse]:
        params = {
            "peer_id": peer_id,
        }
        url = self.build_query_url("messages.getConversationMembers", params)
        data = await self.query(url, method="GET")

        if data.get("error"):
            # нет прав доступа
            return None

        return ConversationMembersResponse(data)
