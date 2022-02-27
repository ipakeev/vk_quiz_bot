import typing
from typing import Optional

from gino import Gino
from sqlalchemy.engine.url import URL

if typing.TYPE_CHECKING:
    from app.web.app import Application

db = Gino()


def register_models() -> None:
    """
    Для удобства работы с alembic и вообще для создания всех gino моделей сразу импортируем их здесь.
    """
    import app.admin.models as m1
    import app.game.models as m2
    import app.quiz.models as m3
    import app.vk.models as m4
    _ = m1
    _ = m2
    _ = m3
    _ = m4


class Database:
    db: Optional[Gino]

    def __init__(self, app: "Application"):
        self.app = app
        self.is_connected = False
        register_models()

    async def connect(self, *_, **__):
        if self.is_connected:
            self.app.logger.warning("connection already exist!")
            return

        self.db = db
        await self.db.set_bind(
            URL(
                drivername="asyncpg",
                host=self.app.config.database.host,
                database=self.app.config.database.database,
                username=self.app.config.database.user,
                password=self.app.config.database.password,
                port=self.app.config.database.port,
            ),
            min_size=1,
            max_size=1,
            echo=False,
        )
        await self.db.gino.create_all()
        self.is_connected = True

    async def disconnect(self, *_, **__):
        if not self.is_connected:
            self.app.logger.warning("connection is not exist!")
            return

        await self.db.pop_bind().close()
        self.is_connected = False
