from app.base.accessor import BaseAccessor
from app.store.vk_api.responses import ConversationMembersResponse


class GameAccessor(BaseAccessor):

    async def create_game(self, peer_id, members: ConversationMembersResponse):
        pass
