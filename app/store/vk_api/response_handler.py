from dataclasses import dataclass

from app.database.accessor import BaseAccessor
from app.store.vk_api.long_poller import build_query


class ChatInviteUserEvent:

    def __init__(self, update: dict):
        self.date: int = update["object"]["message"]["date"]
        self.from_id: int = update["object"]["message"]["from_id"]
        self.member_id: int = update["object"]["message"]["action"]["member_id"]
        self.peer_id: int = update["object"]["message"]["peer_id"]

    @property
    def params(self) -> dict:
        return dict(member_id=self.member_id, peer_id=self.peer_id)


class VKResponseHandler(BaseAccessor):

    async def handle_updates(self, raw_updates: list[dict]):
        for update in raw_updates:
            event_type = update.get("type")
            if event_type == "message_new":
                if update.get("object", {}).get("message", {}).get("action", {}).get("type") == "chat_invite_user":
                    e = ChatInviteUserEvent(update)
                    await self.app.store.vk_messenger.send(e.params, "Для начала назначьте меня администратором чата.")
            # updates.append(
            #     Update(
            #         type=update["type"],
            #         object=UpdateObject(
            #             id=update["object"]["id"],
            #             user_id=update["object"]["user_id"],
            #             body=update["object"]["body"],
            #         ),
            #     )
            # )
