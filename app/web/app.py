import pathlib
from typing import Union
import logging
from aiohttp.web import (
    Application as AiohttpApplication,
    View as AiohttpView,
    Request as AiohttpRequest,
)
from aiohttp_apispec import setup_aiohttp_apispec
from aiohttp_session import setup as setup_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from app.database.database import Database
from app.store.store import Store
from app.web.config import Config, setup_config
from logger import setup_logger


class Application(AiohttpApplication):
    config: Config
    logger: logging.Logger
    database: Database
    store: Store


class Request(AiohttpRequest):

    @property
    def app(self) -> Application:
        return super().app()


class View(AiohttpView):
    @property
    def request(self) -> Request:
        return super().request

    @property
    def store(self) -> Store:
        return self.request.app.store

    @property
    def data(self) -> dict:
        return self.request.get("data", {})


def setup_app(config_file: Union[str, pathlib.Path]) -> Application:
    from app.web.routes import setup_routes
    from app.web.middlewares import setup_middlewares

    app = Application()

    setup_config(app, config_file)
    setup_logger(app)
    setup_session(app, EncryptedCookieStorage(app.config.web_session.key))
    setup_routes(app)
    setup_aiohttp_apispec(app,
                          title=app.config.swagger.title,
                          url=app.config.swagger.json_url,
                          swagger_path=app.config.swagger.path)
    setup_middlewares(app)

    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.store = Store(app)
    app.on_cleanup.append(app.database.disconnect)

    return app
