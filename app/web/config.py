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


@dataclass
class DatabaseConfig:
    host: str
    port: int
    username: str
    password: str
    database: str


@dataclass
class RedisConfig:
    host: str
    port: int
    db: int


@dataclass
class VKBotConfig:
    token: str
    group_id: int
    animate_timer: bool  # set False to avoid 'Flood control: too much messages sent to user'
    beautiful: bool
    sleep_before_show_variants: int
    sleep_before_show_answer: int
    long_poller_wait: int
    updates_poller_queue_poller_sleep: float
    updates_poller_gc_sleep: float
    bot_gc_sleep: float


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
