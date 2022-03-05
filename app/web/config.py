import pathlib
import typing
from dataclasses import dataclass
from typing import Union

import yaml

if typing.TYPE_CHECKING:
    from app.web.app import Application


@dataclass
class WebSessionConfig:
    key: str


@dataclass
class AdminConfig:
    email: str
    password: str


@dataclass(init=False)
class DatabaseConfig:
    host: str
    port: int
    username: str
    password: str
    database: str

    # validate
    def __init__(self, host: str, port: int, username: str, password: str, database: str):
        self.host = str(host)
        self.port = int(port)
        self.username = str(username)
        self.password = str(password)
        self.database = str(database)


@dataclass(init=False)
class RedisConfig:
    host: str
    port: int
    db: int

    # validate
    def __init__(self, host: str, port: int, db: int):
        self.host = str(host)
        self.port = int(port)
        self.db = int(db)


@dataclass(init=False)
class VKBotConfig:
    token: str
    group_id: int

    # validate: group type is int
    def __init__(self, token: str, group_id: int):
        self.token = token
        self.group_id = int(group_id)


@dataclass
class LoggerConfig:
    name: str
    file: str
    format: str


@dataclass
class SwaggerConfig:
    title: str
    json_url: str
    path: str


@dataclass
class Config:
    web_session: WebSessionConfig
    admin: AdminConfig
    database: DatabaseConfig
    redis: RedisConfig
    vk_bot: VKBotConfig
    logger: LoggerConfig
    swagger: SwaggerConfig


def setup_config(app: "Application", config_file: Union[str, pathlib.Path]):
    with open(config_file) as f:
        raw_yaml = yaml.safe_load(f)

    app.config = Config(
        web_session=WebSessionConfig(**raw_yaml["web_session"]),
        admin=AdminConfig(**raw_yaml["admin"]),
        database=DatabaseConfig(**raw_yaml["database"]),
        redis=RedisConfig(**raw_yaml["redis"]),
        vk_bot=VKBotConfig(**raw_yaml["vk_bot"]),
        logger=LoggerConfig(**raw_yaml["logger"]),
        swagger=SwaggerConfig(**raw_yaml["swagger"])
    )
