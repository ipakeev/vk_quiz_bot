import typing
from asyncio import Queue

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from app.store.admin.accessor import AdminAccessor
        from app.store.quiz.accessor import QuizAccessor
        from app.store.game.accessor import StateAccessor, GameAccessor
        from app.store.vk_api.long_poller import VKLongPoller
        from app.store.vk_api.messenger import VKMessenger
        from app.store.vk_api.updates_poller import VKUpdatesPoller
        from app.store.vk_api.bot import VKBot

        self.quiz = QuizAccessor(app)
        self.admins = AdminAccessor(app)
        self.states = StateAccessor(app)
        self.games = GameAccessor(app)
        self.vk_long_poller = VKLongPoller(app)
        self.vk_updates_queue = Queue()
        self.vk_messenger = VKMessenger(app)
        self.vk_updates_poller = VKUpdatesPoller(app)
        self.vk_bot = VKBot(app)
