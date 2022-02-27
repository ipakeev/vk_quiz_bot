import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from app.store.admin.accessor import AdminAccessor
        from app.store.quiz.accessor import QuizAccessor
        from app.store.vk_api.long_poller import VKLongPoller
        from app.store.vk_api.messenger import VKMessenger
        from app.store.vk_api.response_handler import VKResponseHandler
        # from app.store.bot.manager import BotManager

        self.quiz = QuizAccessor(app)
        self.admins = AdminAccessor(app)
        self.vk_long_poller = VKLongPoller(app)
        self.vk_messenger = VKMessenger(app)
        self.vk_response_handler = VKResponseHandler(app)
        # self.bots_manager = BotManager(app)
