import json
import random
import typing
from typing import Optional

from aiohttp import ClientSession, TCPConnector

from app.base.accessor import BaseAccessor
from app.store.vk_api.keyboard import Keyboard, Carousel
from app.store.vk_api.responses import VKUser

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
        # TODO: catch exceptions
        async with self.session.request(method, url) as resp:
            if not resp.ok:
                self.app.logger.warning(f"status={resp.status}, method={method}, url={url}")
                return {}

            data = await resp.json()
            self.app.logger.debug(f"status={resp.status}, method={method}")
            return data

    async def send_sticker(self, chat_id: int, sticker_id: int):
        """
        В сообщении со стикером можно посылать клавиатуру, но нельзя редактировать,
        поэтому, чтобы исключить ошибки, реализуем метод отправки ТОЛЬКО стикера
        (без клавиатуры или карусели).
        """
        params = {
            "peer_id": chat_id,
            "random_id": random.randint(1, 2 ** 32),
            "sticker_id": sticker_id,
        }

        url = self.build_query_url("messages.send", params)
        response = await self.query(url, method="POST")

        if response.get("error"):
            self.app.logger.warning(f"sticker not sent: {response}, params=({params})")
            return False
        else:
            self.app.logger.debug("sticker sent")
            return True

    async def send(self,
                   chat_id: int,
                   message: str,
                   photo: Optional[str] = None,
                   keyboard: Optional[Keyboard] = None,
                   carousel: Optional[Carousel] = None) -> bool:
        assert not (keyboard and carousel)
        params = {
            "peer_id": chat_id,
            "random_id": random.randint(1, 2 ** 32),
            "message": message,
        }
        if photo:
            params["attachment"] = photo
        if keyboard:
            params["keyboard"] = json.dumps(keyboard.as_dict())
        if carousel:
            params["template"] = json.dumps(carousel.as_dict())

        url = self.build_query_url("messages.send", params)
        response = await self.query(url, method="POST")

        if response.get("error"):
            self.app.logger.warning(f"msg not sent: {response}, params=({params})")
            return False
        else:
            self.app.logger.debug("msg sent")
            return True

    async def edit(self,
                   chat_id: int,
                   conversation_message_id: int,
                   message: str,
                   photo: Optional[str] = None,
                   keyboard: Optional[Keyboard] = None,
                   carousel: Optional[Carousel] = None) -> bool:
        assert not (keyboard and carousel)
        params = {
            "peer_id": chat_id,
            "conversation_message_id": conversation_message_id,
            "message": message,
        }
        if photo:
            params["attachment"] = photo
        if keyboard:
            params["keyboard"] = json.dumps(keyboard.as_dict())
        if carousel:
            params["template"] = json.dumps(carousel.as_dict())

        url = self.build_query_url("messages.edit", params)
        response = await self.query(url, method="POST")

        if response.get("error"):
            self.app.logger.warning(f"msg not edited: {response}, params=({params})")
            return False
        else:
            self.app.logger.debug("msg edited")
            return True

    async def delete(self, chat_id: int, conversation_message_id: int):
        params = {
            "peer_id": chat_id,
            "cmids": str(conversation_message_id),
            "delete_for_all": 1,
        }

        url = self.build_query_url("messages.delete", params)
        response = await self.query(url, method="POST")

        if response.get("error"):
            self.app.logger.warning(f"msg not deleted: {response}, params=({params})")
            return False
        else:
            self.app.logger.debug("msg deleted")
            return True

    async def event_ok(self, chat_id: int, user_id: int, event_id: str) -> bool:
        params = {
            "peer_id": chat_id,
            "user_id": user_id,
            "event_id": event_id,
        }
        url = self.build_query_url("messages.sendMessageEventAnswer", params)
        response = await self.query(url, method="POST")

        if response.get("error"):
            self.app.logger.warning(f"error on event_ok: {response}, params=({params})")
            return False
        else:
            self.app.logger.debug("event_ok")
            return True

    async def show_snackbar(self, chat_id: int, user_id: int, event_id: str, message: str) -> bool:
        params = {
            "peer_id": chat_id,
            "user_id": user_id,
            "event_id": event_id,
            "event_data": json.dumps({
                "type": "show_snackbar",
                "text": message,
            }),
        }
        url = self.build_query_url("messages.sendMessageEventAnswer", params)
        response = await self.query(url, method="POST")

        if response.get("error"):
            self.app.logger.warning(f"error on show_snackbar: {response}, params=({params})")
            return False
        else:
            self.app.logger.debug("show_snackbar")
            return True

    async def get_user_info(self, user_id: int) -> Optional[VKUser]:
        params = {
            "user_ids": str(user_id),
        }
        url = self.build_query_url("users.get", params)
        response = await self.query(url, method="GET")

        if response.get("error"):
            self.app.logger.warning(f"error on get_user_info: {response}, params=({params})")
            return None
        else:
            self.app.logger.debug(f"{user_id}: {response}")
            return VKUser(response["response"][0])
