import typing
from typing import Optional

from gino import Gino
from redis import Redis
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
    _ = m1
    _ = m2
    _ = m3


class Database:
    db: Optional[Gino]
    redis: Optional[Redis]

    def __init__(self, app: "Application"):
        self.app = app
        register_models()

    async def connect(self, *_, **__):
        self.app.logger.info("connecting to the database")

        self.db = db
        await self.db.set_bind(
            URL(
                drivername="asyncpg",
                username=self.app.config.database.username,
                password=self.app.config.database.password,
                host=self.app.config.database.host,
                port=self.app.config.database.port,
                database=self.app.config.database.database,
            ),
            min_size=1,
            max_size=1,
            echo=False,
        )
        await self.db.gino.create_all()

        self.redis = Redis(host=self.app.config.redis.host,
                           port=self.app.config.redis.port,
                           db=self.app.config.redis.db)

    async def disconnect(self, *_, **__):
        self.app.logger.info("disconnecting from the database")

        await self.db.pop_bind().close()
        self.redis.close()
